import logging
from datetime import datetime
from typing import List

from src.alerter.alerts.alert import Alert
from src.channels_manager.apis.email_api import EmailApi
from src.channels_manager.channels.channel import Channel
from src.utils.constants.channels import (EMAIL_TEXT_TEMPLATE,
                                          EMAIL_HTML_TEMPLATE)
from src.utils.data import RequestStatus


class EmailChannel(Channel):
    def __init__(self, channel_name: str, channel_id: str,
                 logger: logging.Logger, emails_to: List[str],
                 email_api: EmailApi):
        super().__init__(channel_name, channel_id, logger)

        self._emails_to = emails_to
        self._email_api = email_api

    def alert(self, alert: Alert) -> RequestStatus:
        subject = "PANIC {}".format(alert.severity)
        html_email_message = EMAIL_HTML_TEMPLATE.format(
            alert_code=alert.alert_code.value, severity=alert.severity,
            message=alert.message,
            date_time=datetime.fromtimestamp(alert.timestamp),
            parent_id=alert.parent_id, origin_id=alert.origin_id
        )
        plain_email_message = EMAIL_TEXT_TEMPLATE.format(
            alert_code=alert.alert_code.value, severity=alert.severity,
            message=alert.message,
            date_time=datetime.fromtimestamp(alert.timestamp),
            parent_id=alert.parent_id, origin_id=alert.origin_id
        )
        self._logger.debug("Formatted email template")
        self._logger.debug("Sending alert to the channel's destination emails")
        self._logger.debug("Destination Emails: %s",
                           self._emails_to)
        try:
            for to_address in self._emails_to:
                self._logger.debug("Sending alert to %s", to_address)
                self._email_api.send_email_with_html(
                    subject, html_email_message, plain_email_message,
                    to_address)
                self._logger.debug("Sent alert to %s", to_address)
            self._logger.debug("Sent alert to all the emails in the channel")
            return RequestStatus.SUCCESS
        except Exception as e:
            self._logger.error("Error when sending %s to Email channel %s",
                               alert.alert_code.name, self.__str__())
            self._logger.exception(e)
            return RequestStatus.FAILED
