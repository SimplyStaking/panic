from json import JSONDecodeError
from typing import List, Any


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
        code = 5000
        super().__init__(message, code)


class MessageWasNotDeliveredException(PANICException):
    def __init__(self, err):
        message = "Message could not be delivered. Error: {}".format(err)
        code = 5001
        super().__init__(message, code)


class NoMetricsGivenException(PANICException):
    def __init__(self, message: str) -> None:
        code = 5002
        super().__init__(message, code)


class MetricNotFoundException(PANICException):
    def __init__(self, metric, endpoint) -> None:
        message = "Could not find metric {} at endpoint {}".format(metric,
                                                                   endpoint)
        code = 5003
        super().__init__(message, code)


class SystemIsDownException(PANICException):
    def __init__(self, system_name) -> None:
        message = "System {} is unreachable".format(system_name)
        code = 5004
        super().__init__(message, code)


class DataReadingException(PANICException):
    def __init__(self, monitor_name, source) -> None:
        message = "{} experienced errors when reading data from {}" \
            .format(monitor_name, source)
        code = 5005
        super().__init__(message, code)


class CannotAccessGitHubPageException(PANICException):
    def __init__(self, page) -> None:
        message = "Cannot access GitHub page {}".format(page)
        code = 5006
        super().__init__(message, code)


class GitHubAPICallException(PANICException):
    def __init__(self, err) -> None:
        message = "Error in API Call: {}".format(err)
        code = 5007
        super().__init__(message, code)


class ReceivedUnexpectedDataException(PANICException):
    def __init__(self, receiver) -> None:
        message = "{} received unexpected data".format(receiver)
        code = 5008
        super().__init__(message, code)


class InvalidUrlException(PANICException):
    def __init__(self, url) -> None:
        message = "Invalid URL '{}'".format(url)
        code = 5009
        super().__init__(message, code)


class ParentIdsMissMatchInAlertsConfiguration(PANICException):
    def __init__(self, err) -> None:
        message = "{} Error alerts do not have the same parent_ids".format(err)
        code = 5010
        super().__init__(message, code)


class MissingKeyInConfigException(PANICException):
    def __init__(self, key: str, config_file: str):
        message = "Expected {} field in the {} config".format(key, config_file)
        code = 5011
        super().__init__(message, code)


class JSONDecodeException(PANICException):
    def __init__(self, exception: JSONDecodeError) -> None:
        code = 5012
        super().__init__(exception.msg, code)


class BlankCredentialException(PANICException):
    def __init__(self, blank_credentials: List[str]) -> None:
        message = \
            "Tried to initiate a connection with a blank or NoneType {}".format(
                ",".join(blank_credentials)
            )
        code = 5013
        super().__init__(message, code)


class EnabledSourceIsEmptyException(PANICException):
    def __init__(self, source: str, monitorable_name: str) -> None:
        message = "Enabled source {} is empty for node {}".format(
            source, monitorable_name)
        code = 5014
        super().__init__(message, code)


class NodeIsDownException(PANICException):
    def __init__(self, node_name) -> None:
        message = "Node {} is unreachable".format(node_name)
        code = 5015
        super().__init__(message, code)


class InvalidDictSchemaException(PANICException):
    def __init__(self, dict_name: str) -> None:
        message = "{} does not obey the valid schema.".format(dict_name)
        code = 5016
        super().__init__(message, code)


class ComponentNotGivenEnoughDataSourcesException(PANICException):
    def __init__(self, component: str, field: str) -> None:
        message = "{} was not given enough data sources. {} is empty.".format(
            component, field)
        code = 5017
        super().__init__(message, code)


class CouldNotRetrieveContractsException(PANICException):
    def __init__(self, component: str, url: str) -> None:
        message = "{} could not retrieve contracts data from {}.".format(
            component, url)
        code = 5018
        super().__init__(message, code)


class NoSyncedDataSourceWasAccessibleException(PANICException):
    def __init__(self, component: str, sources_type: str) -> None:
        message = "{} could not access any synced {}.".format(component,
                                                              sources_type)
        code = 5019
        super().__init__(message, code)
