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
        msg = '{} {} - {}'.format(self.channel_name, alert.severity.upper(),
                                  alert.message)
        try:
            print(msg)
            sys.stdout.flush()
            self.logger.info("Sent {} to console channel {}.".format(
                alert.alert_code.name, self))
            return RequestStatus.SUCCESS
        except Exception as e:
            self.logger.error(
                "Error when sending {} to console channel {}.".format(
                    alert.alert_code.name, self))
            self.logger.exception(e)
            return RequestStatus.FAILED
