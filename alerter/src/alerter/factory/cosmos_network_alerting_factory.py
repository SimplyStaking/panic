import logging
from typing import Dict, Any, Type, List

from src.alerter.alert_severities import Severity
from src.alerter.factory.alerting_factory import AlertingFactory
from src.alerter.grouped_alerts_metric_code.network.cosmos_network_metric_code \
    import GroupedCosmosNetworkAlertsMetricCode as AlertsMetricCode
from src.utils.types import ErrorAlert, ErrorSolvedAlert


class CosmosNetworkAlertingFactory(AlertingFactory):
    """
    This class is in charge of alerting and managing the alerting state for the
    cosmos network alerter. The alerting_state dict is to be structured as
    follows:
    {
        <parent_id>: {
            Optional[warning_sent]: {
                GroupedCosmosNetworkAlertsMetricCode.value: bool
            },
            Optional[critical_sent]: {
                GroupedCosmosNetworkAlertsMetricCode.value: bool
            },
            Optional[error_sent]: {
                GroupedCosmosNetworkAlertsMetricCode.value: bool
            },
            Optional[any_severity_sent]: {
                GroupedCosmosNetworkAlertsMetricCode.value: bool
            },
            Optional[warning_window_timer]: {
                GroupedCosmosNetworkAlertsMetricCode.value: TimedTaskTracker
            },
            Optional[critical_window_timer]: {
                GroupedCosmosNetworkAlertsMetricCode.value: TimedTaskTracker
            },
            Optional[critical_repeat_timer]: {
                GroupedCosmosNetworkAlertsMetricCode.value: TimedTaskLimiter
            },
            Optional[warning_occurrences_in_period_tracker]: {
                GroupedCosmosNetworkAlertsMetricCode.value:
                    OccurrencesInTimePeriodTracker
            },
            Optional[critical_occurrences_in_period_tracker]: {
                GroupedCosmosNetworkAlertsMetricCode.value:
                    OccurrencesInTimePeriodTracker
            },
            active_proposals: Dict,
        }
    }
    """

    def __init__(self, component_logger: logging.Logger) -> None:
        super().__init__(component_logger)

    def create_alerting_state(self, parent_id: str) -> None:
        """
        If no state is already stored, this function will create a new alerting
        state for a network.
        :param parent_id: The id of the chain
        :return: None
        """
        if parent_id not in self.alerting_state:
            error_sent = {
                AlertsMetricCode.NoSyncedCosmosRestSource.value: False,
                AlertsMetricCode.CosmosNetworkDataNotObtained.value: False,
            }
            self.alerting_state[parent_id] = {
                'error_sent': error_sent,
                'active_proposals': {},
            }

    def remove_chain_alerting_state(self, parent_id: str) -> None:
        """
        This function deletes an entire alerting state for a chain.
        :param parent_id: The id of the chain to be deleted
        :return: None
        """
        if parent_id in self.alerting_state:
            del self.alerting_state[parent_id]

    @staticmethod
    def _proposal_id_valid(proposal_id: Any) -> bool:
        return isinstance(proposal_id, int)

    def add_active_proposal(self, parent_id: str, proposal: Dict,
                            proposal_id: int) -> None:
        """
        This function adds a proposal to the active list if the alerting state
        for the chain has already been created.
        :param parent_id: The chain identifier
        :param proposal: The proposal to store
        :param proposal_id: The proposal identifier
        :return: None
        """
        if not self._proposal_id_valid(proposal_id):
            return

        if parent_id in self.alerting_state:
            active_proposals = self.alerting_state[parent_id][
                'active_proposals']
            active_proposals[proposal_id] = proposal

    def remove_active_proposal(self, parent_id: str, proposal_id: int) -> None:
        """
        This function removes a proposal from the active list if the alerting
        state was created and the proposal_id is in the active list.
        :param parent_id: The chain identifier
        :param proposal_id: The proposal identifier
        :return:
        """
        if not self._proposal_id_valid(proposal_id):
            return

        if (parent_id in self.alerting_state
                and proposal_id in self.alerting_state[parent_id][
                    'active_proposals']):
            del self.alerting_state[parent_id]['active_proposals'][proposal_id]

    def proposal_active(self, parent_id: str, proposal_id: int) -> bool:
        """
        Given the parent_id and the proposal_id, this function checks if a
        proposal is in the active list for the chain.
        :param parent_id: The chain identifier
        :param proposal_id: The proposal identifier
        :return: True if proposal in the active list
               : False otherwise
        """
        if parent_id in self.alerting_state:
            active_proposals = self.alerting_state[parent_id][
                'active_proposals']
            return proposal_id in active_proposals

        return False

    def classify_error_alert(
            self, error_code_to_detect: int, error_alert: Type[ErrorAlert],
            error_solved_alert: Type[ErrorSolvedAlert], data_for_alerting: List,
            parent_id: str, monitorable_id: str, monitorable_name: str,
            monitoring_timestamp: float, metric_name: str,
            error_message: str = "", resolved_message: str = "",
            received_error_code: int = None,
    ) -> None:
        """
        This function is an adaptation of the classify_error_alert function of
        the AlertingFactory class. This is needed because the
        CosmosNetworkAlertingFactory class stores the alerting state
        differently.
        :param received_error_code: The code associated with the received error
        if any. If no errors are received this should be set to None.
        :param error_code_to_detect: The error code to detect in order to raise
        the error alert
        :param error_alert: The error alert to be raised if detected
        :param error_solved_alert: The alert to be raised if the error is solved
        :param data_for_alerting: The list to be appended with alerts
        :param parent_id: The id of the base chain
        :param monitorable_id: The id of the monitorable
        :param metric_name: The name of the metric
        :param monitorable_name: The name of the monitorable
        :param monitoring_timestamp: The data timestamp
        :param error_message: The alert's message when an error is raised
        :param resolved_message: The alert's message when an error is resolved
        :param received_error_code: The received error code
        :return: None
        """

        error_sent = self.alerting_state[parent_id]['error_sent'][metric_name]

        if error_sent and received_error_code != error_code_to_detect:
            alert = error_solved_alert(
                monitorable_name, resolved_message, Severity.INFO.value,
                monitoring_timestamp, parent_id, monitorable_id
            )
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug("Successfully classified alert %s",
                                        alert.alert_data)
            self.alerting_state[parent_id]['error_sent'][metric_name] = False
        elif received_error_code == error_code_to_detect:
            alert = error_alert(
                monitorable_name, error_message, Severity.ERROR.value,
                monitoring_timestamp, parent_id, monitorable_id
            )
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug("Successfully classified alert %s",
                                        alert.alert_data)
            self.alerting_state[parent_id]['error_sent'][metric_name] = True
