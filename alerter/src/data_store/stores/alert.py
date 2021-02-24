import json
import logging
from datetime import datetime
from typing import Dict

import pika.exceptions

from src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from src.data_store.mongo.mongo_api import MongoApi
from src.data_store.stores.store import Store
from src.utils.constants import (STORE_EXCHANGE, HEALTH_CHECK_EXCHANGE,
                                 ALERT_STORE_INPUT_QUEUE,
                                 ALERT_STORE_INPUT_ROUTING_KEY)
from src.utils.exceptions import (ReceivedUnexpectedDataException,
                                  MessageWasNotDeliveredException)


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
                                       exchange_type='direct', passive=False,
                                       durable=True, auto_delete=False,
                                       internal=False)
        self.rabbitmq.queue_declare(ALERT_STORE_INPUT_QUEUE, passive=False,
                                    durable=True, exclusive=False,
                                    auto_delete=False)
        self.rabbitmq.queue_bind(queue=ALERT_STORE_INPUT_QUEUE,
                                 exchange=STORE_EXCHANGE,
                                 routing_key=ALERT_STORE_INPUT_ROUTING_KEY)

        # Set producing configuration for heartbeat
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, 'topic', False,
                                       True, False, False)

    def _listen_for_data(self) -> None:
        self.rabbitmq.basic_consume(queue=ALERT_STORE_INPUT_QUEUE,
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
        alert_data = json.loads(body.decode())
        self.logger.info("Received %s. Now processing this data.", alert_data)

        processing_error = False
        try:
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
                        'timestamp': str(alert['timestamp']),
                    }
                },
                '$min': {'first': alert['timestamp']},
                '$max': {'last': alert['timestamp']},
                '$inc': {'n_alerts': 1},
            }
        )
