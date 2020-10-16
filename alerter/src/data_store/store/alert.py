
import logging
import json
import pika
import pika.exceptions
from datetime import datetime
from typing import Dict, List, Optional
from alerter.src.utils.exceptions import SavingMetricsToMongoException
from alerter.src.data_store.mongo.mongo_api import MongoApi
from alerter.src.data_store.redis.redis_api import RedisApi
from alerter.src.data_store.redis.store_keys import Keys
from alerter.src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from alerter.src.utils.types import AlertDataType
from alerter.src.data_store.store.store import Store

class AlertStore(Store):
    def __init__(self, logger: logging.Logger) -> None:
        super().__init__(logger)

    """
        Initialize the necessary data for rabbitmq to be able to reach the data
        store as well as appropriately communicate with it.

        Creates an exchange named `store` of type `topic`
        Declares a queue named `alerts_store_queue` and binds it to exchange
        `store` with a routing key `alert_route` meaning anything
        coming from the alert_router containing an alert will be stored.
    """
    def _initialize_store(self) -> None:
        self.rabbitmq.connect_till_successful()
        self.rabbitmq.exchange_declare(exchange='store', exchange_type='topic',
            passive=False, durable=True, auto_delete=False, internal=False)
        self.rabbitmq.queue_declare('alerts_store_queue', passive=False, \
            durable=True, exclusive=False, auto_delete=False)
        self.rabbitmq.queue_bind(queue='alerts_store_queue', exchange='store',
            routing_key='alert_route')
        self.rabbitmq.queue_purge(queue='alerts_store_queue')

    def _start_listening(self) -> None:
        self._mongo = MongoApi(logger=self.logger, db_name=self.mongo_db, \
            host=self.mongo_ip, port=self.mongo_port)
        self.rabbitmq.basic_consume(queue='alerts_store_queue', \
            on_message_callback=self._process_data, auto_ack=False, \
                exclusive=False, consumer_tag=None)
        self.rabbitmq.start_consuming()

    """
        Processes the data being received, from the queue. There is only one
        type of data that is going to be received which is an alert. All
        alerts will be stored in mongo, there isn't a need to store them in
        redis.
    """
    def _process_data(self, ch, method: pika.spec.Basic.Deliver, \
        properties: pika.spec.BasicProperties, body: bytes) -> None:
        alert_data = json.loads(body.decode())
        self._process_mongo_store(alert_data)
        self.rabbitmq.basic_ack(method.delivery_tag, False)

    """
        Updating mongo with alerts using a size-based document with 1000 entries
        Collection is the name of the chain, with document type alert as only
        alerts will be stored. Mongo will keep adding new alerts to a document
        until it's reached 1000 entries at which point mongo will create a new
        document and repeat the process.

        Origin is the object the alert is associated with e.g cosmos_node_2.
        Alert name is the configured alerts e.g Validator Missing Blocks
        Message contains the specific details e.g Missed 40 Blocks in a row
        Timestamp is the time of alerting

        $min/$max are used for data aggregation
        $min is the timestamp of the first alert
        $max is the timestamp of the last alert entered
        $inc increments n_alerts by one each time an alert is added
    """
    def _process_mongo_store(self, alert: AlertDataType) -> None:
        try:
            self.mongo.update_one(alert['chain_name'],
                {'doc_type': 'alert', 'n_alerts': {'$lt': 1000}},
                {'$push': { 'alerts': {
                    'origin': alert['origin'],  
                    'alert_name': alert['alert_name'],
                    'severity': alert['severity'],
                    'message': alert['message'],
                    'timestamp': alert['timestamp'],
                    }
                },
                    '$min': {'first': alert['timestamp']},
                    '$max': {'last': alert['timestamp']},
                    '$inc': {'n_alerts': 1},
                }
            )
        except Exception as e:
            self.logger.error(e)
            raise SavingMetricsToMongoException(
                'Failed to save alert to Mongo.')
