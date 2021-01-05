import logging

from src.alerter.alerts.alert import Alert
from src.channels_manager.apis.pagerduty_api import PagerDutyApi
from src.channels_manager.channels import Channel
from src.utils.data import RequestStatus
from src.utils.types import PagerDutySeverities


class PagerDutyChannel(Channel):
    def __init__(self, channel_name: str, channel_id: str,
                 logger: logging.Logger, pagerduty_api: PagerDutyApi):
        super().__init__(channel_name, channel_id,
                         logger.getChild(channel_name))

        self._pager_duty_api = pagerduty_api

    def alert(self, alert: Alert) -> RequestStatus:
        severity = PagerDutySeverities(alert.severity.lower())

        try:
            self._pager_duty_api.trigger(alert.message, severity,
                                         alert.origin_id, alert.timestamp)
            self.logger.info("Sent %s to PagerDuty channel %s",
                             alert.alert_code.name, self.__str__())
            return RequestStatus.SUCCESS
        except Exception as e:
            self.logger.error("Error when sending %s to PagerDuty channel %s",
                              alert.alert_code.name, self.__str__())
            self.logger.exception(e)
            return RequestStatus.FAILED
