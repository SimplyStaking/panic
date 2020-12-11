import logging

from src.alerter.alerts.alert import Alert
from src.channels_manager.channels.channel import Channel
from src.utils.alert import Severity
from src.utils.data import RequestStatus


class LogChannel(Channel):

    def __init__(self, channel_name: str, channel_id: str,
                 channel_logger: logging.Logger,
                 alerts_logger: logging.Logger) -> None:
        super().__init__(channel_name, channel_id, channel_logger)

        self._alerts_logger = alerts_logger

    def alert(self, alert: Alert) -> RequestStatus:
        alert_severity = alert.severity.upper()
        msg = "{} {} - {}".format(self.channel_name, alert_severity,
                                  alert.message)
        try:
            if alert_severity == Severity.INFO.value:
                self._alerts_logger.info(msg)
                self.logger.info("Sent %s to log channel %s.",
                                 alert.alert_code.name, self.__str__())
                return RequestStatus.SUCCESS
            elif alert_severity == Severity.CRITICAL.value:
                self._alerts_logger.critical(msg)
                self.logger.info("Sent %s to log channel %s.",
                                 alert.alert_code.name, self.__str__())
                return RequestStatus.SUCCESS
            elif alert_severity == Severity.WARNING.value:
                self._alerts_logger.warning(msg)
                self.logger.info("Sent %s to log channel %s.",
                                 alert.alert_code.name, self.__str__())
                return RequestStatus.SUCCESS
            elif alert_severity == Severity.ERROR.value:
                self._alerts_logger.error(msg)
                self.logger.info("Sent %s to log channel %s.",
                                 alert.alert_code.name, self.__str__())
                return RequestStatus.SUCCESS
            else:
                self.logger.error("Alert has invalid severity %s",
                                  alert_severity)
                return RequestStatus.FAILED
        except Exception as e:
            self.logger.error(
                "Error when sending %s to log channel %s.",
                alert.alert_code.name, self.__str__())
            self.logger.exception(e)
            return RequestStatus.FAILED
