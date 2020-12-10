from src.alerter.alerts.alert import Alert
from src.channels_manager.channels import Channel
from src.utils.data import RequestStatus


class PagerDutyChannel(Channel):
    def alert(self, alert: Alert) -> RequestStatus:
        pass