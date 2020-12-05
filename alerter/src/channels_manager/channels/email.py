import logging

from src.alerter.alerts.alert import Alert
from src.channels_manager.apis.email_api import EmailApi
from src.channels_manager.channels.channel import Channel
from src.configs.email_channel import EmailChannelConfig
from src.utils.data import RequestStatus

_EMAIL_TEMPLATE = """<style type="text/css">
.email {font-family: sans-serif}
.tg  {border:none; border-spacing:0;border-collapse: collapse;}
.tg td{border-style:none;border-width:0px;overflow:hidden; padding:10px 5px;word-break:normal;}
.tg th{border-style:none;border-width:0px;overflow:hidden;padding:10px 5px;word-break:normal;text-align:left;background-color:lightgray;}
@media screen and (max-width: 767px) {.tg {width: auto !important;}.tg col {width: auto !important;}.tg-wrap {overflow-x: auto;-webkit-overflow-scrolling: touch;}}</style>
<div class="email">
<h2>PANIC Alert</h2>
<p>An alert was generated with the following details:</p>
<div class="tg-wrap"><table class="tg">
<tbody>
  <tr>
    <th>Alert Code:</th>
    <td>{alert_code}</td>
  </tr>
  <tr>
    <th>Severity:</th>
    <td>{severity}</td>
  </tr>
  <tr>
    <th>Message:</th>
    <td>{message}</td>
  </tr>
  <tr>
    <th>Timestamp:</th>
    <td>{timestamp}</td>
  </tr>
  <tr>
    <th>Parent ID:</th>
    <td>{parent_id}</td>
  </tr>
  <tr>
    <th>Origin ID:</th>
    <td>{origin_id}</td>
  </tr>
</tbody>
</table></div>
</div>"""


class EmailChannel(Channel):
    def __init__(self, channel_name: str, channel_id: str,
                 logger: logging.Logger, email_config: EmailChannelConfig):
        super().__init__(channel_name, channel_id, logger)
        self._config = email_config
        self._email_api = EmailApi(self._config.smtp, self._config.email_from,
                                   self._config.username, self._config.password)

    def alert(self, alert: Alert) -> RequestStatus:
        subject = "PANIC {}".format(alert.severity)
        email_message = _EMAIL_TEMPLATE.format(
            alert_code=alert.alert_code.value, severity=alert.severity,
            message=alert.message, timestamp=alert.timestamp,
            parent_id=alert.parent_id, origin_id=alert.origin_id
        )
        self._logger.debug("Formatted email template")
        self._logger.info("Sending alert to the channel's destination emails")
        self._logger.debug("Destination Emails: %s",
                           self._config.emails_to)
        try:
            for to_address in self._config.emails_to:
                self._logger.debug("Sending alert to %s", to_address)
                self._email_api.send_email(subject, email_message, to_address)
                self._logger.debug("Sent alert to %s", to_address)
            self._logger.info("Sent alert to all the emails in the channel")
            return RequestStatus.SUCCESS
        except Exception as e:
            self._logger.error("Error when sending %s to Email channel %s",
                               alert.alert_code.name, self)
            self._logger.exception(e)
            return RequestStatus.FAILED
