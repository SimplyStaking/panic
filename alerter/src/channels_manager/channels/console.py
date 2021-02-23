import logging
import sys

from src.alerter.alerts.alert import Alert
from src.channels_manager.channels.channel import Channel
from src.utils.data import RequestStatus


class ConsoleChannel(Channel):

    def __init__(self, channel_name: str, channel_id: str,
                 logger: logging.Logger) -> None:
        super().__init__(channel_name, channel_id, logger)

    def alert(self, alert: Alert) -> RequestStatus:
        msg = "PANIC {} - {}".format(alert.severity.upper(), alert.message)
        try:
            print(msg)
            sys.stdout.flush()
            self.logger.debug("Sent %s to console.", alert.alert_code.name)
            return RequestStatus.SUCCESS
        except Exception as e:
            self.logger.error("Error when sending %s to console.",
                              alert.alert_code.name, self.__str__())
            self.logger.exception(e)
            return RequestStatus.FAILED
