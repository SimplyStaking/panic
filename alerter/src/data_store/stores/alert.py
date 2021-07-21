import json
import logging
from datetime import datetime
from typing import Dict

import pika.exceptions

from src.alerter.alert_code import InternalAlertCode
from src.alerter.alert_severities import Severity
from src.alerter.alerters.github import GithubAlerter
from src.alerter.alerters.node.chainlink import ChainlinkNodeAlerter
from src.alerter.alerters.system import SystemAlerter
from src.data_store.mongo.mongo_api import MongoApi
from src.data_store.redis.store_keys import Keys
from src.data_store.stores.store import Store
from src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from src.utils.constants.data import (EXPIRE_METRICS,
                                      CHAINLINK_METRICS_TO_STORE,
                                      SYSTEM_METRICS_TO_STORE)
from src.utils.constants.rabbitmq import (STORE_EXCHANGE, HEALTH_CHECK_EXCHANGE,
                                          ALERT_STORE_INPUT_QUEUE_NAME,
                                          ALERT_STORE_INPUT_ROUTING_KEY, TOPIC)
from src.utils.exceptions import (MessageWasNotDeliveredException)


class AlertStore(Store):
    def __init__(self, name: str, logger: logging.Logger,
                 rabbitmq: RabbitMQApi) -> None:
        super().__init__(name, logger, rabbitmq)
        self._mongo = MongoApi(logger=self.logger.getChild(MongoApi.__name__),
                               db_name=self.mongo_db, host=self.mongo_ip,
                               port=self.mongo_port)

    def _initialise_rabbitmq(self) -> None:
        """
        Initialise the necessary data for rabbitmq to be able to reach the data
        store as well as appropriately communicate with it.

        Creates a store exchange of type `direct`
        Declares a queue named `alerts_store_queue` and binds it to the store
        exchange with a routing key `alert`.
        """
        self.rabbitmq.connect_till_successful()
        self.rabbitmq.exchange_declare(exchange=STORE_EXCHANGE,
                                       exchange_type=TOPIC, passive=False,
                                       durable=True, auto_delete=False,
                                       internal=False)
        self.rabbitmq.queue_declare(ALERT_STORE_INPUT_QUEUE_NAME, passive=False,
                                    durable=True, exclusive=False,
                                    auto_delete=False)
        self.rabbitmq.queue_bind(queue=ALERT_STORE_INPUT_QUEUE_NAME,
                                 exchange=STORE_EXCHANGE,
                                 routing_key=ALERT_STORE_INPUT_ROUTING_KEY)

        # Set producing configuration for heartbeat
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)

    def _listen_for_data(self) -> None:
        self.rabbitmq.basic_consume(queue=ALERT_STORE_INPUT_QUEUE_NAME,
                                    on_message_callback=self._process_data,
                                    auto_ack=False, exclusive=False,
                                    consumer_tag=None)
        self.rabbitmq.start_consuming()

    def _process_data(self,
                      ch: pika.adapters.blocking_connection.BlockingChannel,
                      method: pika.spec.Basic.Deliver,
                      properties: pika.spec.BasicProperties,
                      body: bytes) -> None:
        """
        Processes the data being received, from the queue. There is only one
        type of data that is going to be received which is an alert. All
        alerts will be stored in mongo, there isn't a need to store them in
        redis. If successful, a heartbeat will be sent.
        """
        alert_data = json.loads(body)
        self.logger.debug("Received %s. Now processing this data.", alert_data)

        processing_error = False
        try:
            self._process_redis_store(alert_data)
            self._process_mongo_store(alert_data)
        except KeyError as e:
            self.logger.error("Error when parsing %s.", alert_data)
            self.logger.exception(e)
            processing_error = True
        except Exception as e:
            self.logger.exception(e)
            processing_error = True

        self.rabbitmq.basic_ack(method.delivery_tag, False)

        # Send a heartbeat only if there were no errors
        if not processing_error:
            try:
                heartbeat = {
                    'component_name': self.name,
                    'is_alive': True,
                    'timestamp': datetime.now().timestamp()
                }
                self._send_heartbeat(heartbeat)
            except MessageWasNotDeliveredException as e:
                self.logger.exception(e)
            except Exception as e:
                # For any other exception raise it.
                raise e

    def _process_mongo_store(self, alert: Dict) -> None:
        """
        Updating mongo with alerts using a size-based document with 1000
        entries. Collection is the name of the chain, with document type alert
        as only alerts will be stored. Mongo will keep adding new alerts to a
        document until it's reached 1000 entries at which point mongo will
        create a new document and repeat the process.

        Origin is the object the alert is associated with e.g cosmos_node_2.
        Alert name is the configured alerts e.g Validator Missing Blocks
        Message contains the specific details e.g Missed 40 Blocks in a row
        Timestamp is the time of alerting

        $min/$max are used for data aggregation
        $min is the timestamp of the first alert
        $max is the timestamp of the last alert entered
        $inc increments n_alerts by one each time an alert is added
        """

        # Do not save the internal alerts into Mongo as they aren't useful to
        # the user
        if alert['severity'] != Severity.INTERNAL.value:
            self.mongo.update_one(
                alert['parent_id'],
                {
                    'doc_type': 'alert',
                    'n_alerts': {'$lt': 1000}
                }, {
                    '$push': {
                        'alerts': {
                            'origin': alert['origin_id'],
                            'alert_name': alert['alert_code']['name'],
                            'severity': alert['severity'],
                            'message': alert['message'],
                            'metric': alert['metric'],
                            'timestamp': alert['timestamp'],
                        }
                    },
                    '$min': {'first': alert['timestamp']},
                    '$max': {'last': alert['timestamp']},
                    '$inc': {'n_alerts': 1},
                }
            )

    def _process_redis_store(self, alert: Dict) -> None:
        if alert['severity'] == Severity.INTERNAL.value:
            if alert['alert_code']['code'] == \
                    InternalAlertCode.ComponentResetAlert.value and \
                    alert['origin_id'] in [SystemAlerter.__name__,
                                           ChainlinkNodeAlerter.__name__,
                                           GithubAlerter.__name__]:
                """
                The `ComponentResetAlert` indicates that a component or PANIC 
                has restarted. If this component is an alerter, we will reset 
                the relevant component metrics for all chains or for a 
                particular chain, depending on whether the parent_id is None or
                not.
                """
                configuration = {
                    SystemAlerter.__name__: {
                        'metrics_type': 'system',
                        'redis_key_index': 'alert_system'
                    },
                    ChainlinkNodeAlerter.__name__: {
                        'metrics_type': 'chainlink node metrics',
                        'redis_key_index': 'alert_cl_node'
                    },
                    GithubAlerter.__name__: {
                        'metrics_type': 'github',
                        'redis_key_index': 'alert_github2'
                    }
                }
                alerter_type = alert['origin_id']
                metrics_type = configuration[alerter_type]['metrics_type']
                redis_key_index = configuration[alerter_type]['redis_key_index']
                if alert['parent_id'] is None:
                    self.logger.debug("Resetting the %s metrics for all "
                                      "chains.", metrics_type)
                    parent_hash = Keys.get_hash_parent_raw()
                    chain_hashes_list = self.redis.get_keys_unsafe(
                        '*' + parent_hash + '*')

                    # Go through all the chains that are in REDIS
                    for chain in chain_hashes_list:
                        # For each chain we need to load all the keys and only
                        # delete the ones that match the pattern `alert_system*`
                        # or `alert_cl_node*`, depending on the alerter_type.
                        # Note, REDIS doesn't support this natively
                        for key in self.redis.hkeys(chain):
                            # We only want to delete alert keys
                            if redis_key_index in key and self.redis.hexists(
                                    chain, key):
                                self.redis.hremove(chain, key)
                else:
                    self.logger.debug("Resetting %s metrics for chain %s.",
                                      metrics_type, alert['parent_id'])
                    """
                    For the specified chain we need to load all the keys and 
                    only delete the ones that match the pattern `alert_system*`
                    or `alert_cl_node*`, depending on the alerter_type.
                    Note, REDIS doesn't support this natively.
                    """
                    chain_hash = Keys.get_hash_parent(alert['parent_id'])
                    for key in self.redis.hkeys(chain_hash):
                        # We only want to delete alert keys
                        if redis_key_index in key and self.redis.hexists(
                                chain_hash, key):
                            self.redis.hremove(chain_hash, key)
        else:
            """
            If the alert is not of severity Internal, the metric needs to be
            stored in REDIS, this will be used for easier querying on the UI.
            """
            self.logger.debug("Saving alert in REDIS: %s.", alert)
            metric_data = {'severity': alert['severity'],
                           'message': alert['message'],
                           'expiry': None}
            key = alert['origin_id']

            # Check if this metric cannot be overwritten and has to be deleted
            if alert['metric'] in EXPIRE_METRICS:
                metric_data['expiry'] = alert['timestamp'] + 600

            if alert['metric'] in CHAINLINK_METRICS_TO_STORE:
                self.redis.hset(
                    Keys.get_hash_parent(alert['parent_id']),
                    eval('Keys.get_alert_cl_{}(key)'.format(alert['metric'])),
                    json.dumps(metric_data)
                )
            elif alert['metric'] in SYSTEM_METRICS_TO_STORE:
                self.redis.hset(
                    Keys.get_hash_parent(alert['parent_id']),
                    eval('Keys.get_alert_{}(key)'.format(alert['metric'])),
                    json.dumps(metric_data)
                )
            else:
                self.redis.hset(
                    Keys.get_hash_parent(alert['parent_id']),
                    eval('Keys.get_alert_{}(key)'.format(alert['metric'])),
                    json.dumps(metric_data)
                )
