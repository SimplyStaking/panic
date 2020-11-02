from enum import Enum, auto, unique


@unique
class Channel(Enum):
    """
    Alert channels and the routing keys for each channel manager are defined
    here
    """
    EMAIL = "email"
    TELEGRAM = "telegram"
    TWILIO = "twilio"
    OPS_GENIE = "ops_genie"
    PAGER_DUTY = "pager_duty"
    CONSOLE = "cosnole"

    @property
    def routing_key(self):
        return f"channel.{self.value}"
