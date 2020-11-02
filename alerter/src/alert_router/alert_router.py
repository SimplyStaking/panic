from logging import Logger

from src.alert import Alert
from src.message_broker.rabbitmq import RabbitMQApi


class AlertRouter:
    def __init__(self, logger: Logger, alert_input_channel: str,
                 rabbit_ip: str):
        self._logger = logger
        self._alert_input_channel = alert_input_channel
        self._rabbit = RabbitMQApi(logger.getChild("rabbitmq"), host=rabbit_ip)

    def _process_alert(self, alert: Alert):
        pass

    def _start_listening(self) -> None:
        self._rabbit.basic_consume(queue=self._alert_input_channel,
                                    on_message_callback=self._process_alert,
                                    auto_ack=False,
                                    exclusive=False, consumer_tag=None)
        self.rabbitmq.start_consuming()

    def run(self):
