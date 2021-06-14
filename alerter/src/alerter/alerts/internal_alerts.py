from src.alerter.alert_code import InternalAlertCode
from src.alerter.alert_severities import Severity
from src.alerter.alerts.alert import Alert
from src.alerter.alert_metric_code import InternalAlertMetricCode

"""
Such internal alerts are used to notify that a component has been reset. 
Normally such alerts are raised only when a desirable action is needed. 
Currently, they are used by the Alerter Managers to notify the Alert Store that
that some alert metrics need to be reset in Redis.
"""


class ComponentResetAlert(Alert):
    """
    If a component which is associated with more than 1 chain is reset,
    parent_id should be set to None.
    origin_name: The name of the component which was reset
    parent_id: The id of the chain associated with the component being reset
    chain_name: The name of the chain associated with the component being reset
    origin_id: The type of the component which was reset
    timestamp: Time of the resetting.
    """

    def __init__(self, origin_name: str, timestamp: float, origin_id: str,
                 parent_id: str = None, chain_name: str = None) -> None:
        if parent_id and chain_name:
            msg = "Component: {} has been reset for {}.".format(origin_name,
                                                                chain_name)
        else:
            msg = "Component: {} has been reset for all chains.".format(
                origin_name)

        super().__init__(
            InternalAlertCode.ComponentResetAlert, msg, Severity.INTERNAL.value,
            timestamp, parent_id, origin_id,
            InternalAlertMetricCode.ComponentReset)
