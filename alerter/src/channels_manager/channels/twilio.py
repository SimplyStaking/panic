import logging

from src.channels_manager.apis.twilio_api import TwilioApi
from src.channels_manager.channels.channel import Channel
from src.utils.data import RequestStatus


class TwilioChannel(Channel):

    def __init__(self, channel_name: str, channel_id: str,
                 logger: logging.Logger, twilio_api: TwilioApi) -> None:
        super().__init__(channel_name, channel_id,
                         logger.getChild(channel_name))

        self._twilio_api = twilio_api

    def alert(self, call_from: str, call_to: str, twiml: str,
              twiml_is_url: bool) -> RequestStatus:

        self.logger.info("Twilio is now calling %s.", call_to)

        try:
            self._twilio_api.dial_number(call_from, call_to, twiml,
                                         twiml_is_url)
            return RequestStatus.SUCCESS
        except Exception as e:
            self.logger.exception(e)
            self.logger.error("Error when calling %s.", call_to)
            return RequestStatus.FAILED
