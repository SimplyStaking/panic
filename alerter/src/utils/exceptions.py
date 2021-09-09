from json import JSONDecodeError
from typing import List, Any
from .exception_codes import ExceptionCodes


class PANICException(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code
        super().__init__(self.message, self.code)

    def __eq__(self, other: Any) -> bool:
        return self.__dict__ == other.__dict__

    def __hash__(self):
        return hash((self.message, self.code))


class ConnectionNotInitialisedException(PANICException):
    def __init__(self, component):
        message = "Did not initialise a connection with {}" \
            .format(component)
        super().__init__(
            message, ExceptionCodes.ConnectionNotInitialisedException.value)


class MessageWasNotDeliveredException(PANICException):
    def __init__(self, err):
        message = "Message could not be delivered. Error: {}".format(err)
        super().__init__(
            message, ExceptionCodes.MessageWasNotDeliveredException.value)


class NoMetricsGivenException(PANICException):

    def __init__(self, message: str) -> None:
        super().__init__(message, ExceptionCodes.NoMetricsGivenException.value)


class MetricNotFoundException(PANICException):

    def __init__(self, metric, endpoint) -> None:
        message = "Could not find metric {} at endpoint {}" \
            .format(metric, endpoint)
        super().__init__(message, ExceptionCodes.MetricNotFoundException.value)


class SystemIsDownException(PANICException):

    def __init__(self, system_name) -> None:
        message = "System {} is unreachable".format(system_name)
        super().__init__(message, ExceptionCodes.SystemIsDownException.value)


class DataReadingException(PANICException):

    def __init__(self, monitor_name, source) -> None:
        message = "{} experienced errors when reading data from {}" \
            .format(monitor_name, source)
        super().__init__(message, ExceptionCodes.DataReadingException.value)


class CannotAccessGitHubPageException(PANICException):

    def __init__(self, page) -> None:
        message = "Cannot access GitHub page {}".format(page)
        super().__init__(message,
                         ExceptionCodes.CannotAccessGitHubPageException.value)


class GitHubAPICallException(PANICException):

    def __init__(self, err) -> None:
        message = "Error in API Call: {}".format(err)
        super().__init__(message, ExceptionCodes.GitHubAPICallException.value)


class ReceivedUnexpectedDataException(PANICException):

    def __init__(self, receiver) -> None:
        message = "{} received unexpected data".format(receiver)
        super().__init__(message,
                         ExceptionCodes.ReceivedUnexpectedDataException.value)


class InvalidUrlException(PANICException):

    def __init__(self, url) -> None:
        message = "Invalid URL '{}'".format(url)
        super().__init__(message, ExceptionCodes.InvalidUrlException.value)


class ParentIdsMissMatchInAlertsConfiguration(PANICException):
    def __init__(self, err) -> None:
        message = "{} Error alerts do not have the same parent_ids".format(err)
        super().__init__(
            message,
            ExceptionCodes.ParentIdsMissMatchInAlertsConfiguration.value)


class MissingKeyInConfigException(PANICException):
    def __init__(self, key: str, config_file: str):
        message = "Expected {} field in the {} config".format(key, config_file)
        super().__init__(
            message, ExceptionCodes.MissingKeyInConfigException.value)


class JSONDecodeException(PANICException):

    def __init__(self, exception: JSONDecodeError) -> None:
        super().__init__(exception.msg,
                         ExceptionCodes.JSONDecodeException.value)


class BlankCredentialException(PANICException):
    def __init__(self, blank_credentials: List[str]) -> None:
        message = \
            "Tried to initiate a connection with a blank or NoneType {}".format(
                ",".join(blank_credentials)
            )
        super().__init__(message, ExceptionCodes.BlankCredentialException.value)


class EnabledSourceIsEmptyException(PANICException):
    def __init__(self, source: str, monitorable_name: str) -> None:
        message = "Enabled source {} is empty for node {}".format(
            source, monitorable_name)
        super().__init__(message,
                         ExceptionCodes.EnabledSourceIsEmptyException.value)


class NodeIsDownException(PANICException):

    def __init__(self, node_name) -> None:
        message = "Node {} is unreachable".format(node_name)
        super().__init__(message, ExceptionCodes.NodeIsDownException.value)


class InvalidDictSchemaException(PANICException):

    def __init__(self, dict_name: str) -> None:
        message = "{} does not obey the valid schema.".format(dict_name)
        super().__init__(message,
                         ExceptionCodes.InvalidDictSchemaException.value)


class ComponentNotGivenEnoughDataSourcesException(PANICException):

    def __init__(self, component: str, field: str) -> None:
        message = "{} was not given enough data sources. {} is empty.".format(
            component, field)
        super().__init__(
            message,
            ExceptionCodes.ComponentNotGivenEnoughDataSourcesException.value)


class CouldNotRetrieveContractsException(PANICException):

    def __init__(self, component: str, url: str) -> None:
        message = "{} could not retrieve contracts data from {}.".format(
            component, url)
        super().__init__(
            message, ExceptionCodes.CouldNotRetrieveContractsException.value)


class NoSyncedDataSourceWasAccessibleException(PANICException):

    def __init__(self, component: str, sources_type: str) -> None:
        message = "{} could not access any synced {}.".format(component,
                                                              sources_type)
        super().__init__(
            message,
            ExceptionCodes.NoSyncedDataSourceWasAccessibleException.value)


class ErrorRetrievingChainlinkContractData(PANICException):
    def __init__(self, component: str, parent_id: str) -> None:
        message = "{} could not retrieve chainlink contract data for the "
        "chain {}.".format(component, parent_id)
        super().__init__(
            message, ExceptionCodes.ErrorRetrievingChainlinkContractData.value)
