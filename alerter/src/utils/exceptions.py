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
    code = 5000

    def __init__(self, component):
        message = "Did not initialise a connection with {}".format(component)
        super().__init__(message, self.code)


class MessageWasNotDeliveredException(PANICException):
    code = 5001

    def __init__(self, err):
        message = "Message could not be delivered. Error: {}".format(err)
        super().__init__(message, self.code)


class NoMetricsGivenException(PANICException):
    code = 5002

    def __init__(self, message: str) -> None:
        super().__init__(message, self.code)


class MetricNotFoundException(PANICException):
    code = 5003

    def __init__(self, metric, endpoint) -> None:
        message = "Could not find metric {} at endpoint {}".format(metric,
                                                                   endpoint)
        super().__init__(message, self.code)


class SystemIsDownException(PANICException):
    code = 5004

    def __init__(self, system_name) -> None:
        message = "System {} is unreachable".format(system_name)
        super().__init__(message, self.code)


class DataReadingException(PANICException):
    code = 5005

    def __init__(self, monitor_name, source) -> None:
        message = "{} experienced errors when reading data from {}".format(
            monitor_name, source)
        super().__init__(message, self.code)


class CannotAccessGitHubPageException(PANICException):
    code = 5006

    def __init__(self, page) -> None:
        message = "Cannot access GitHub page {}".format(page)
        super().__init__(message, self.code)


class GitHubAPICallException(PANICException):
    code = 5007

    def __init__(self, err) -> None:
        message = "Error in API Call: {}".format(err)
        super().__init__(message, self.code)


class ReceivedUnexpectedDataException(PANICException):
    code = 5008

    def __init__(self, receiver) -> None:
        message = "{} received unexpected data".format(receiver)
        super().__init__(message, self.code)


class InvalidUrlException(PANICException):
    code = 5009

    def __init__(self, url) -> None:
        message = "Invalid URL '{}'".format(url)
        super().__init__(message, self.code)


class ParentIdsMissMatchInAlertsConfiguration(PANICException):
    code = 5010

    def __init__(self, err) -> None:
        message = "{} Error, alerts do not have the same parent_ids".format(err)
        super().__init__(message, self.code)


class MissingKeyInConfigException(PANICException):
    code = 5011

    def __init__(self, key: str, config_file: str):
        message = "Expected {} field in the {} config".format(key, config_file)
        super().__init__(message, self.code)


class JSONDecodeException(PANICException):
    code = 5012

    def __init__(self, exception: JSONDecodeError) -> None:
        super().__init__(exception.msg, self.code)


class BlankCredentialException(PANICException):
    code = 5013

    def __init__(self, blank_credentials: List[str]) -> None:
        message = (
            "Tried to initiate a connection with a blank or NoneType {}".format(
                ",".join(blank_credentials)
            )
        )
        super().__init__(message, self.code)


class EnabledSourceIsEmptyException(PANICException):
    code = 5014

    def __init__(self, source: str, monitorable_name: str) -> None:
        message = "Enabled source {} is empty for node {}".format(
            source, monitorable_name)
        super().__init__(message, self.code)


class NodeIsDownException(PANICException):
    code = 5015

    def __init__(self, node_name) -> None:
        message = "Node {} is unreachable".format(node_name)
        super().__init__(message, self.code)


class InvalidDictSchemaException(PANICException):
    code = 5016

    def __init__(self, dict_name: str) -> None:
        message = "{} does not obey the valid schema.".format(dict_name)
        super().__init__(message, self.code)


class ComponentNotGivenEnoughDataSourcesException(PANICException):
    code = 5017

    def __init__(self, component: str, field: str) -> None:
        message = "{} was not given enough data sources. {} is empty.".format(
            component, field)
        super().__init__(message, self.code)


class CouldNotRetrieveContractsException(PANICException):
    code = 5018

    def __init__(self, component: str, url: str) -> None:
        message = "{} could not retrieve contracts data from {}.".format(
            component, url)
        super().__init__(message, self.code)


class NoSyncedDataSourceWasAccessibleException(PANICException):
    code = 5019

    def __init__(self, component: str, sources_type: str) -> None:
        message = "{} could not access any synced {}.".format(component,
                                                              sources_type)
        super().__init__(message, self.code)


class DockerHubAPICallException(PANICException):
    code = 5020

    def __init__(self):
        message = "API call came back empty, repo probably does not exist."
        super().__init__(message, self.code)


class CannotAccessDockerHubPageException(PANICException):
    code = 5021

    def __init__(self, page) -> None:
        message = "Cannot access Dockerhub page {}".format(page)
        super().__init__(message, self.code)


class CosmosSDKVersionIncompatibleException(PANICException):
    code = 5022

    def __init__(self, node_name: str, supported_version: str) -> None:
        message = (
            "The Cosmos SDK version of node {} is not compatible with "
            "supported version(s) {}".format(node_name, supported_version)
        )
        super().__init__(message, self.code)


class CosmosRestServerDataCouldNotBeObtained(PANICException):
    code = 5023

    def __init__(self, node_name: str) -> None:
        message = (
            "PANIC cannot obtain Rest data for {} either due to Cosmos SDK or "
            "Tendermint incompatibility issues in the node used as data "
            "source. Please check the logs of {} to detect which node is "
            "incompatible and disable it from being a data source. If no "
            "other compatible data source can be given (not even {}), please "
            "disable Rest monitoring altogether for {}. ".format(
                node_name, node_name, node_name, node_name))
        super().__init__(message, self.code)


class CosmosRestServerApiCallException(PANICException):
    code = 5024

    def __init__(self, api_call: str, error_message: str) -> None:
        message = "Cosmos Rest Server call {} failed. Error: {}".format(
            api_call, error_message)
        super().__init__(message, self.code)


class IncorrectJSONRetrievedException(PANICException):
    code = 5025

    def __init__(self, api_name: str, error_message: str) -> None:
        message = "Invalid JSON structure retrieved from {}. Error: {}".format(
            api_name, error_message)
        super().__init__(message, self.code)


class CannotConnectWithDataSourceException(PANICException):
    code = 5026

    def __init__(self, monitor_name: str, source_name: str,
                 error_message: str) -> None:
        message = "{} cannot connect with data source {}. Error: {}".format(
            monitor_name, source_name, error_message)
        super().__init__(message, self.code)


class CosmosNetworkDataCouldNotBeObtained(PANICException):
    code = 5027

    def __init__(self) -> None:
        message = (
            "PANIC cannot obtain network data from COSMOS Rest Server either "
            "due to Cosmos SDK or Tendermint incompatibility issues in the "
            "nodes used as data sources. Please check the logs to detect which "
            "nodes are incompatible and disable them from being a data source. "
            "If no other compatible data source can be given, please disable "
            "network monitoring."
        )
        super().__init__(message, self.code)


class TendermintRPCIncompatibleException(PANICException):
    code = 5028

    def __init__(self, node_name: str) -> None:
        message = (
            "The Tendermint RPC version of node {} is not compatible with "
            "PANIC".format(node_name)
        )
        super().__init__(message, self.code)


class TendermintRPCDataCouldNotBeObtained(PANICException):
    code = 5029

    def __init__(self, node_name: str) -> None:
        message = (
            "PANIC cannot obtain Tendermint RPC data for {} either due to "
            "Tendermint or Tendermint RPC incompatibility issues in the node "
            "used as data source. Please check the logs of {} to detect which "
            "node is incompatible and disable it from being a data source. If "
            "no other compatible data source can be given (not even {}), "
            "please disable Tendermint RPC monitoring altogether for "
            "{}.".format(node_name, node_name, node_name, node_name)
        )
        super().__init__(message, self.code)


class TendermintRPCCallException(PANICException):
    code = 5030

    def __init__(self, api_call: str, error_message: str) -> None:
        message = "Tendermint RPC call {} failed. Error: {}".format(
            api_call, error_message)
        super().__init__(message, self.code)
