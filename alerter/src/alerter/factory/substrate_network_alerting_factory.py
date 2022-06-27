import logging
from typing import Type, List, Callable, Any

from src.alerter.alert_severities import Severity
from src.alerter.factory.alerting_factory import AlertingFactory
from src.alerter.grouped_alerts_metric_code.network. \
    substrate_network_metric_code \
    import GroupedSubstrateNetworkAlertsMetricCode as AlertsMetricCode
from src.utils.exceptions import SubstrateApiIsNotReachableException
from src.utils.types import ErrorAlert, ErrorSolvedAlert, ConditionalAlert


class SubstrateNetworkAlertingFactory(AlertingFactory):
    """
    This class is in charge of alerting and managing the alerting state for the
    substrate network alerter. The alerting_state dict is to be structured as
    follows:
    {
        <parent_id>: {
            Optional[any_severity_sent]: {
                GroupedSubstrateNetworkAlertsMetricCode.value: bool
            },
            Optional[error_sent]: {
                GroupedSubstrateNetworkAlertsMetricCode.value: bool
            }
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
            any_severity_sent = {
                AlertsMetricCode.GrandpaIsStalled.value: False,
            }
            error_sent = {
                AlertsMetricCode.NoSyncedSubstrateWebSocketDataSource.value:
                    False,
                AlertsMetricCode.SubstrateNetworkDataNotObtained.value: False,
                AlertsMetricCode.SubstrateApiNotReachable.value: False,
            }
            self.alerting_state[parent_id] = {
                'any_severity_sent': any_severity_sent,
                'error_sent': error_sent,
            }

    def remove_chain_alerting_state(self, parent_id: str) -> None:
        """
        This function deletes an entire alerting state for a chain.
        :param parent_id: The id of the chain to be deleted
        :return: None
        """
        if parent_id in self.alerting_state:
            del self.alerting_state[parent_id]

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
        SubstrateNetworkAlertingFactory class stores the alerting state
        differently. This function also checks if the Substrate API is not
        reachable error was sent so that we do not classify other error alerts
        if this is the case.
        :param error_code_to_detect: The error code to detect in order to raise
        the error alert
        :param error_alert: The error alert to be raised if detected
        :param error_solved_alert: The alert to be raised if the error is solved
        :param data_for_alerting: The list to be appended with alerts
        :param parent_id: The id of the base chain
        :param monitorable_id: The id of the monitorable
        :param monitorable_name: The name of the monitorable
        :param monitoring_timestamp: The data timestamp
        :param metric_name: The name of the metric
        :param error_message: The alert's message when an error is raised
        :param resolved_message: The alert's message when an error is resolved
        :param received_error_code: The code associated with the received error
        if any. If no errors are received this should be set to None.
        :return: None
        """

        substrate_api_error_sent = self.alerting_state[parent_id]['error_sent'][
            AlertsMetricCode.SubstrateApiNotReachable.value]

        # For this to work, we need to classify the Substrate API Not Reachable
        # alert before every other possible alert
        if (substrate_api_error_sent and received_error_code ==
                SubstrateApiIsNotReachableException.code):
            return

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

    def classify_solvable_conditional_alert_no_repetition(
            self, parent_id: str, monitorable_id: str, metric_name: str,
            condition_true_alert: Type[ConditionalAlert],
            condition_function: Callable, condition_fn_args: List[Any],
            true_alert_args: List[Any], data_for_alerting: List,
            solved_alert: Type[ConditionalAlert], solved_alert_args: List[Any]
    ) -> None:
        """
        This function is an adaptation of the
        classify_solvable_conditional_alert_no_repetition function of the
        AlertingFactory class. This is needed because the
        SubstrateNetworkAlertingFactory class stores the alerting state
        differently.
        :param parent_id: The id of the base chain
        :param monitorable_id: The id of the monitorable
        :param metric_name: The name of the metric
        :param condition_true_alert: The alert to be raised if the condition
        is true
        :param condition_function: The function to be used to check the
        conditional statement
        :param condition_fn_args: The arguments to pass to the
        conditional function
        :param true_alert_args: The arguments to pass to the true alert
        :param data_for_alerting: The list to be appended with alerts
        :param solved_alert: The alert to be raised if the condition is false
        :param solved_alert_args: The arguments to pass to the solved alert
        :return: None
        """
        alert_sent = self.alerting_state[parent_id]['any_severity_sent']
        if condition_function(*condition_fn_args):
            if not alert_sent[metric_name]:
                alert = condition_true_alert(*true_alert_args)
                data_for_alerting.append(alert.alert_data)
                self.component_logger.debug("Successfully classified alert %s",
                                            alert.alert_data)
                self.alerting_state[parent_id]['any_severity_sent'][
                    metric_name] = True
        else:
            if alert_sent[metric_name]:
                alert = solved_alert(*solved_alert_args)
                data_for_alerting.append(alert.alert_data)
                self.component_logger.debug("Successfully classified alert %s",
                                            alert.alert_data)
                self.alerting_state[parent_id]['any_severity_sent'][
                    metric_name] = False
