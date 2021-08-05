import logging

from src.alerter.alerts.alert import Alert
from src.channels_manager.apis.slack_bot_api import SlackBotApi
from src.channels_manager.channels.channel import Channel
from src.utils.data import RequestStatus


class SlackChannel(Channel):

    def __init__(self, channel_name: str, channel_id: str,
                 logger: logging.Logger, slack_bot: SlackBotApi) -> None:
        super().__init__(channel_name, channel_id, logger)

        self._slack_bot = slack_bot

    @property
    def slack_bot(self) -> SlackBotApi:
        return self._slack_bot

    def alert(self, alert: Alert) -> RequestStatus:
        subject = "PANIC {}".format(alert.severity.upper())
        try:
            ret = self._slack_bot.send_message('*{}*: `{}`'.format(
                subject, alert.message))
            self.logger.debug("alert: slack_ret: %s", ret)
            if ret == 'ok':
                self.logger.info("Sent %s to Slack channel %s.",
                                 alert.alert_code.name, self.__str__())
                return RequestStatus.SUCCESS
            else:
                self.logger.error(
                    "Error when sending %s to Slack channel %s: %s.",
                    alert.alert_code.name, self.__str__(), ret)
                return RequestStatus.FAILED
        except Exception as e:
            self.logger.error("Error when sending %s to Slack channel %s.",
                              alert.alert_code.name, self.__str__())
            self.logger.exception(e)
            return RequestStatus.FAILED
