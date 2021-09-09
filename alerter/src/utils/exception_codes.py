from enum import Enum

from src.utils.enum import empty


@empty
class ExceptionCodeEnums(str, Enum):
    """
    No checks are made to ensure all values are unique. You need to make sure
    that no values are duplicated across the subclasses
    """

    @classmethod
    def get_enum_by_value(cls: type, value: str) -> 'AlertCode':
        for class_ in [cls] + cls.__subclasses__():
            try:
                return class_(value)
            except ValueError:
                continue

        raise ValueError(
            "'{}' is not a valid {}".format(value, cls.__name__))


class ExceptionCodes(ExceptionCodeEnums):
    """
    This class is needed as there are multiple instances of error codes being
    declared directly, this will give them more meaning by referencing the
    exact name to retrieve the actual value.
    """
    ConnectionNotInitialisedException = 5000
    MessageWasNotDeliveredException = 5001
    NoMetricsGivenException = 5002
    MetricNotFoundException = 5003
    SystemIsDownException = 5004
    DataReadingException = 5005
    CannotAccessGitHubPageException = 5006
    GitHubAPICallException = 5007
    ReceivedUnexpectedDataException = 5008
    InvalidUrlException = 5009
    ParentIdsMissMatchInAlertsConfiguration = 5010
    MissingKeyInConfigException = 5011
    JSONDecodeException = 5012
    BlankCredentialException = 5013
    EnabledSourceIsEmptyException = 5014
    NodeIsDownException = 5015
    InvalidDictSchemaException = 5016
    ComponentNotGivenEnoughDataSourcesException = 5017
    CouldNotRetrieveContractsException = 5018
    NoSyncedDataSourceWasAccessibleException = 5019
    ErrorRetrievingChainlinkContractData = 5020
