from enum import Enum
from typing import Union, Any, Type

from src.alerter.alerts.contract.chainlink import (
    ErrorNoSyncedDataSources as ClContractErrorNoSyncedDataSources,
    SyncedDataSourcesFound as ClContractSyncedDataSourcesFound,
    ErrorContractsNotRetrieved as ClContractErrorContractsNotRetrieved,
    ContractsNowRetrieved as ClContractContractsNowRetrieved,
    PriceFeedObservationsMissedIncreasedAboveThreshold as
    ClContractPriceFeedObservationsMissedIncreasedAboveThreshold,
    PriceFeedObservedAgain as ClContractPriceFeedObservedAgain,
    PriceFeedDeviationIncreasedAboveThreshold as
    ClContractPriceFeedDeviationIncreasedAboveThreshold,
    PriceFeedDeviationDecreasedBelowThreshold as
    ClContractPriceFeedDeviationDecreasedBelowThreshold,
    ConsensusFailure as ClContractConsensusFailure)
from src.alerter.alerts.network.cosmos import (
    ErrorNoSyncedCosmosRestDataSourcesAlert as
    CosmosNetworkErrorNoSyncedCosmosRestDataSourcesAlert,
    SyncedCosmosRestDataSourcesFoundAlert as
    CosmosNetworkSyncedCosmosRestDataSourcesFoundAlert,
    CosmosNetworkDataCouldNotBeObtainedAlert as
    CosmosNetworkCosmosNetworkDataCouldNotBeObtainedAlert,
    CosmosNetworkDataObtainedAlert as
    CosmosNetworkCosmosNetworkDataObtainedAlert,
    NewProposalSubmittedAlert as CosmosNetworkNewProposalSubmittedAlert,
    ProposalConcludedAlert as CosmosNetworkProposalConcludedAlert
)
from src.alerter.alerts.node.chainlink import (
    NoChangeInHeightAlert as ClNodeNoChangeInHeightAlert,
    BlockHeightUpdatedAlert as ClNodeBlockHeightUpdatedAlert,
    NoChangeInTotalHeadersReceivedAlert as
    ClNodeNoChangeInTotalHeadersReceivedAlert,
    ReceivedANewHeaderAlert as ClNodeReceivedANewHeaderAlert,
    MaxUnconfirmedBlocksIncreasedAboveThresholdAlert as
    ClNodeMaxUnconfirmedBlocksIncreasedAboveThresholdAlert,
    MaxUnconfirmedBlocksDecreasedBelowThresholdAlert as
    ClNodeMaxUnconfirmedBlocksDecreasedBelowThresholdAlert,
    ChangeInSourceNodeAlert as ClNodeChangeInSourceNodeAlert,
    GasBumpIncreasedOverNodeGasPriceLimitAlert as
    ClNodeGasBumpIncreasedOverNodeGasPriceLimitAlert,
    NoOfUnconfirmedTxsIncreasedAboveThresholdAlert as
    ClNodeNoOfUnconfirmedTxsIncreasedAboveThresholdAlert,
    NoOfUnconfirmedTxsDecreasedBelowThresholdAlert as
    ClNodeNoOfUnconfirmedTxsDecreasedBelowThresholdAlert,
    TotalErroredJobRunsDecreasedBelowThresholdAlert as
    ClNodeTotalErroredJobRunsDecreasedBelowThresholdAlert,
    TotalErroredJobRunsIncreasedAboveThresholdAlert as
    ClNodeTotalErroredJobRunsIncreasedAboveThresholdAlert,
    EthBalanceIncreasedAboveThresholdAlert as
    ClNodeEthBalanceIncreasedAboveThresholdAlert,
    EthBalanceDecreasedBelowThresholdAlert as
    ClNodeEthBalanceDecreasedBelowThresholdAlert,
    EthBalanceToppedUpAlert as ClNodeEthBalanceToppedUpAlert,
    InvalidUrlAlert as ClNodeInvalidUrlAlert,
    ValidUrlAlert as ClNodeValidUrlAlert,
    MetricNotFoundErrorAlert as ClNodeMetricNotFoundErrorAlert,
    MetricFoundAlert as ClNodeMetricFoundAlert,
    PrometheusSourceIsDownAlert as ClNodePrometheusSourceIsDownAlert,
    PrometheusSourceBackUpAgainAlert as ClNodePrometheusSourceBackUpAgainAlert,
    NodeStillDownAlert as ClNodeNodeStillDownAlert,
    NodeWentDownAtAlert as ClNodeNodeWentDownAtAlert,
    NodeBackUpAgainAlert as ClNodeNodeBackUpAgainAlert)
from src.alerter.alerts.node.cosmos import (
    PrometheusInvalidUrlAlert as CosmosNodePrometheusInvalidUrlAlert,
    PrometheusValidUrlAlert as CosmosNodePrometheusValidUrlAlert,
    MetricNotFoundErrorAlert as CosmosNodeMetricNotFoundErrorAlert,
    MetricFoundAlert as CosmosNodeMetricFoundAlert,
    NoChangeInHeightAlert as CosmosNodeNoChangeInHeightAlert,
    BlockHeightUpdatedAlert as CosmosNodeBlockHeightUpdatedAlert,
    BlockHeightDifferenceDecreasedBelowThresholdAlert as
    CosmosNodeHeightDifferenceDecrease,
    BlockHeightDifferenceIncreasedAboveThresholdAlert as
    CosmosNodeHeightDifferenceIncrease,
    NodeIsSyncingAlert as CosmosNodeNodeIsSyncingAlert,
    NodeIsNoLongerSyncingAlert as CosmosNodeNodeIsNoLongerSyncingAlert,
    ValidatorIsJailedAlert as CosmosNodeValidatorIsJailedAlert,
    ValidatorIsNoLongerJailedAlert as CosmosNodeValidatorIsNoLongerJailedAlert,
    ValidatorIsActiveAlert as CosmosNodeValidatorIsActiveAlert,
    ValidatorIsNotActiveAlert as CosmosNodeValidatorIsNotActiveAlert,
    ValidatorWasSlashedAlert as CosmosNodeValidatorWasSlashedAlert,
    BlocksMissedDecreasedBelowThresholdAlert as
    CosmosNodeBlocksMissedDecreasedBelowThresholdAlert,
    BlocksMissedIncreasedAboveThresholdAlert as
    CosmosNodeBlocksMissedIncreasedAboveThresholdAlert,
    CosmosRestInvalidUrlAlert as CosmosNodeCosmosRestInvalidUrlAlert,
    CosmosRestValidUrlAlert as CosmosNodeCosmosRestValidUrlAlert,
    ErrorNoSyncedCosmosRestDataSourcesAlert as
    CosmosNodeErrorNoSyncedCosmosRestDataSourcesAlert,
    SyncedCosmosRestDataSourcesFoundAlert as
    CosmosNodeSyncedCosmosRestDataSourcesFoundAlert,
    CosmosRestServerDataCouldNotBeObtainedAlert as
    CosmosNodeCosmosRestServerDataCouldNotBeObtainedAlert,
    CosmosRestServerDataObtainedAlert as
    CosmosNodeCosmosRestServerDataObtainedAlert,
    TendermintRPCInvalidUrlAlert as CosmosNodeTendermintRPCInvalidUrlAlert,
    TendermintRPCValidUrlAlert as CosmosNodeTendermintRPCValidUrlAlert,
    ErrorNoSyncedTendermintRPCDataSourcesAlert as
    CosmosNodeErrorNoSyncedTendermintRPCDataSourcesAlert,
    SyncedTendermintRPCDataSourcesFoundAlert as
    CosmosNodeSyncedTendermintRPCDataSourcesFoundAlert,
    TendermintRPCDataCouldNotBeObtainedAlert as
    CosmosNodeTendermintRPCDataCouldNotBeObtainedAlert,
    TendermintRPCDataObtainedAlert as CosmosNodeTendermintRPCDataObtainedAlert,
    NodeStillDownAlert as CosmosNodeNodeStillDownAlert,
    NodeWentDownAtAlert as CosmosNodeNodeWentDownAtAlert,
    NodeBackUpAgainAlert as CosmosNodeNodeBackUpAgainAlert,
    PrometheusSourceIsDownAlert as CosmosNodePrometheusSourceIsDownAlert,
    PrometheusSourceStillDownAlert as CosmosNodePrometheusSourceStillDownAlert,
    PrometheusSourceBackUpAgainAlert as
    CosmosNodePrometheusSourceBackUpAgainAlert,
    CosmosRestSourceIsDownAlert as CosmosNodeCosmosRestSourceIsDownAlert,
    CosmosRestSourceStillDownAlert as CosmosNodeCosmosRestSourceStillDownAlert,
    CosmosRestSourceBackUpAgainAlert as
    CosmosNodeCosmosRestSourceBackUpAgainAlert,
    TendermintRPCSourceIsDownAlert as CosmosNodeTendermintRPCSourceIsDownAlert,
    TendermintRPCSourceStillDownAlert as
    CosmosNodeTendermintRPCSourceStillDownAlert,
    TendermintRPCSourceBackUpAgainAlert as
    CosmosNodeTendermintRPCSourceBackUpAgainAlert,
)
from src.alerter.alerts.node.evm import (
    NoChangeInBlockHeight as EVMNodeNoChangeInBlockHeight,
    BlockHeightDifferenceIncreasedAboveThresholdAlert as
    EVMNodeBlockHeightDifferenceIncreasedAboveThresholdAlert,
    BlockHeightDifferenceDecreasedBelowThresholdAlert as
    EVMNodeBlockHeightDifferenceDecreasedBelowThresholdAlert,
    BlockHeightUpdatedAlert as EVMNodeBlockHeightUpdatedAlert)
from src.alerter.alerts.system_alerts import (
    OpenFileDescriptorsIncreasedAboveThresholdAlert,
    SystemCPUUsageIncreasedAboveThresholdAlert,
    SystemRAMUsageIncreasedAboveThresholdAlert,
    SystemStorageUsageIncreasedAboveThresholdAlert,
    OpenFileDescriptorsDecreasedBelowThresholdAlert,
    SystemCPUUsageDecreasedBelowThresholdAlert,
    SystemRAMUsageDecreasedBelowThresholdAlert,
    SystemStorageUsageDecreasedBelowThresholdAlert
)
from src.configs.alerts.contract.chainlink import ChainlinkContractAlertsConfig
from src.configs.alerts.network.cosmos import CosmosNetworkAlertsConfig
from src.configs.alerts.node.chainlink import ChainlinkNodeAlertsConfig
from src.configs.alerts.node.cosmos import CosmosNodeAlertsConfig
from src.configs.nodes.node import NodeConfig
from src.configs.repo import GitHubRepoConfig, DockerHubRepoConfig
from src.configs.system import SystemConfig
from src.monitorables.contracts.chainlink.v3 import V3ChainlinkContract
from src.monitorables.contracts.chainlink.v4 import V4ChainlinkContract
from src.monitorables.networks.cosmos import CosmosNetwork
from src.monitorables.nodes.chainlink_node import ChainlinkNode
from src.monitorables.nodes.cosmos_node import CosmosNode
from src.monitorables.nodes.evm_node import EVMNode
from src.monitorables.repo import GitHubRepo, DockerHubRepo
from src.monitorables.system import System

RedisType = Union[bytes, str, int, float]
Monitorable = Union[System, GitHubRepo, DockerHubRepo, ChainlinkNode, EVMNode,
                    CosmosNode, CosmosNetwork, V4ChainlinkContract,
                    V3ChainlinkContract]

# TODO: The below system alerts must be refactored to the types beneath them
#     : when the system alerter is refactored.
IncreasedAboveThresholdSystemAlert = Union[
    OpenFileDescriptorsIncreasedAboveThresholdAlert,
    SystemCPUUsageIncreasedAboveThresholdAlert,
    SystemRAMUsageIncreasedAboveThresholdAlert,
    SystemStorageUsageIncreasedAboveThresholdAlert,
]
DecreasedBelowThresholdSystemAlert = Union[
    OpenFileDescriptorsDecreasedBelowThresholdAlert,
    SystemCPUUsageDecreasedBelowThresholdAlert,
    SystemRAMUsageDecreasedBelowThresholdAlert,
    SystemStorageUsageDecreasedBelowThresholdAlert,
]

ChainlinkNodeNoChangeInAlert = Union[
    ClNodeNoChangeInHeightAlert, ClNodeNoChangeInTotalHeadersReceivedAlert,
    ClNodeNoChangeInHeightAlert, EVMNodeNoChangeInBlockHeight
]
ChainlinkNodeChangeInAlert = Union[
    ClNodeBlockHeightUpdatedAlert, ClNodeReceivedANewHeaderAlert,
    EVMNodeBlockHeightUpdatedAlert
]
CosmosNodeNoChangeInAlert = Union[
    CosmosNodeNoChangeInHeightAlert
]
CosmosNodeChangeInAlert = Union[
    CosmosNodeBlockHeightUpdatedAlert
]
NoChangeInAlert = Union[
    ChainlinkNodeNoChangeInAlert, CosmosNodeNoChangeInAlert,
]
ChangeInAlert = Union[
    ChainlinkNodeChangeInAlert, CosmosNodeChangeInAlert
]

IncreasedAboveThresholdChainlinkNodeAlert = Union[
    ClNodeMaxUnconfirmedBlocksIncreasedAboveThresholdAlert,
    ClNodeNoOfUnconfirmedTxsIncreasedAboveThresholdAlert,
    ClNodeTotalErroredJobRunsIncreasedAboveThresholdAlert,
    ClNodeEthBalanceIncreasedAboveThresholdAlert,
    ClContractPriceFeedObservationsMissedIncreasedAboveThreshold,
    ClContractPriceFeedDeviationIncreasedAboveThreshold,
    EVMNodeBlockHeightDifferenceIncreasedAboveThresholdAlert
]
DecreasedBelowThresholdChainlinkNodeAlert = Union[
    ClNodeMaxUnconfirmedBlocksDecreasedBelowThresholdAlert,
    ClNodeNoOfUnconfirmedTxsDecreasedBelowThresholdAlert,
    ClNodeTotalErroredJobRunsDecreasedBelowThresholdAlert,
    ClNodeEthBalanceDecreasedBelowThresholdAlert,
    ClContractPriceFeedDeviationDecreasedBelowThreshold,
    EVMNodeBlockHeightDifferenceDecreasedBelowThresholdAlert
]
IncreasedAboveThresholdCosmosNodeAlert = Union[
    CosmosNodeHeightDifferenceIncrease,
    CosmosNodeBlocksMissedIncreasedAboveThresholdAlert
]
DecreasedBelowThresholdCosmosNodeAlert = Union[
    CosmosNodeHeightDifferenceDecrease,
    CosmosNodeBlocksMissedDecreasedBelowThresholdAlert
]
IncreasedAboveThresholdAlert = Union[
    IncreasedAboveThresholdChainlinkNodeAlert,
    IncreasedAboveThresholdCosmosNodeAlert
]
DecreasedBelowThresholdAlert = Union[
    DecreasedBelowThresholdChainlinkNodeAlert,
    DecreasedBelowThresholdCosmosNodeAlert
]

ChainlinkNodeConditionalAlert = Union[
    ClNodeChangeInSourceNodeAlert,
    ClNodeGasBumpIncreasedOverNodeGasPriceLimitAlert,
    ClNodeEthBalanceToppedUpAlert, ClNodePrometheusSourceIsDownAlert,
    ClNodePrometheusSourceBackUpAgainAlert, ClContractPriceFeedObservedAgain,
    ClContractConsensusFailure
]
CosmosNodeConditionalAlert = Union[
    CosmosNodeNodeIsSyncingAlert, CosmosNodeNodeIsNoLongerSyncingAlert,
    CosmosNodeValidatorIsJailedAlert, CosmosNodeValidatorIsNoLongerJailedAlert,
    CosmosNodeValidatorIsNotActiveAlert, CosmosNodeValidatorIsActiveAlert,
    CosmosNodeValidatorWasSlashedAlert
]
CosmosNetworkConditionalAlert = Union[
    CosmosNetworkNewProposalSubmittedAlert, CosmosNetworkProposalConcludedAlert
]
ConditionalAlert = Union[
    ChainlinkNodeConditionalAlert, CosmosNodeConditionalAlert,
    CosmosNetworkConditionalAlert
]

ChainlinkNodeErrorAlert = Union[
    ClNodeInvalidUrlAlert, ClNodeMetricNotFoundErrorAlert,
    ClContractErrorNoSyncedDataSources, ClContractErrorContractsNotRetrieved
]
ChainlinkNodeErrorSolvedAlert = Union[
    ClNodeValidUrlAlert, ClNodeMetricFoundAlert,
    ClContractSyncedDataSourcesFound, ClContractContractsNowRetrieved
]
CosmosNodeErrorAlert = Union[
    CosmosNodePrometheusInvalidUrlAlert, CosmosNodeMetricNotFoundErrorAlert,
    CosmosNodeCosmosRestInvalidUrlAlert,
    CosmosNodeErrorNoSyncedCosmosRestDataSourcesAlert,
    CosmosNodeCosmosRestServerDataCouldNotBeObtainedAlert,
    CosmosNodeTendermintRPCInvalidUrlAlert,
    CosmosNodeErrorNoSyncedTendermintRPCDataSourcesAlert,
    CosmosNodeTendermintRPCDataCouldNotBeObtainedAlert,
]
CosmosNodeErrorSolvedAlert = Union[
    CosmosNodePrometheusValidUrlAlert, CosmosNodeMetricFoundAlert,
    CosmosNodeCosmosRestValidUrlAlert,
    CosmosNodeSyncedCosmosRestDataSourcesFoundAlert,
    CosmosNodeCosmosRestServerDataObtainedAlert,
    CosmosNodeTendermintRPCValidUrlAlert,
    CosmosNodeSyncedTendermintRPCDataSourcesFoundAlert,
    CosmosNodeTendermintRPCDataObtainedAlert
]
CosmosNetworkErrorAlert = Union[
    CosmosNetworkCosmosNetworkDataCouldNotBeObtainedAlert,
    CosmosNetworkErrorNoSyncedCosmosRestDataSourcesAlert
]
CosmosNetworkErrorSolvedAlert = Union[
    CosmosNetworkSyncedCosmosRestDataSourcesFoundAlert,
    CosmosNetworkCosmosNetworkDataObtainedAlert
]
ErrorAlert = Union[
    ChainlinkNodeErrorAlert, CosmosNodeErrorAlert, CosmosNetworkErrorAlert
]
ErrorSolvedAlert = Union[
    ChainlinkNodeErrorSolvedAlert, CosmosNodeErrorSolvedAlert,
    CosmosNetworkErrorSolvedAlert
]

DownAlert = Union[
    ClNodeNodeWentDownAtAlert, CosmosNodeNodeWentDownAtAlert,
    CosmosNodePrometheusSourceIsDownAlert,
    CosmosNodeCosmosRestSourceIsDownAlert,
    CosmosNodeTendermintRPCSourceIsDownAlert
]
StillDownAlert = Union[
    ClNodeNodeStillDownAlert, CosmosNodeNodeStillDownAlert,
    CosmosNodePrometheusSourceStillDownAlert,
    CosmosNodeCosmosRestSourceStillDownAlert,
    CosmosNodeTendermintRPCSourceStillDownAlert
]
BackUpAlert = Union[
    ClNodeNodeBackUpAgainAlert, CosmosNodeNodeBackUpAgainAlert,
    CosmosNodePrometheusSourceBackUpAgainAlert,
    CosmosNodeCosmosRestSourceBackUpAgainAlert,
    CosmosNodeTendermintRPCSourceBackUpAgainAlert
]

ChainlinkAlertsConfigs = Union[Type[ChainlinkNodeAlertsConfig],
                               Type[ChainlinkContractAlertsConfig]]
CosmosAlertsConfigs = Union[Type[CosmosNodeAlertsConfig],
                            Type[CosmosNetworkAlertsConfig]]
MonitorableConfig = Union[SystemConfig, GitHubRepoConfig, DockerHubRepoConfig,
                          NodeConfig]

MUTABLE_TYPES = (dict, list, set)


class OpsgenieSeverities(Enum):
    CRITICAL = 'P1'
    ERROR = 'P4'
    WARNING = 'P3'
    INFO = 'P5'


class PagerDutySeverities(Enum):
    CRITICAL = 'critical'
    ERROR = 'error'
    WARNING = 'warning'
    INFO = 'info'


class ChannelTypes(Enum):
    TELEGRAM = 'telegram'
    SLACK = 'slack'
    TWILIO = 'twilio'
    EMAIL = 'email'
    OPSGENIE = 'opsgenie'
    PAGERDUTY = 'pagerduty'
    CONSOLE = 'console'
    LOG = 'log'


class ChannelHandlerTypes(Enum):
    ALERTS = 'alerts'
    COMMANDS = 'commands'


def convert_to_float(value: Union[int, str, float], default_return: Any) -> Any:
    # This function converts a value to float, if the transformation fails it
    # returns a default value
    try:
        return float(value)
    except (TypeError, ValueError):
        return default_return


def convert_to_int(value: Union[int, str, float], default_return: Any) -> Any:
    # This function converts a value to int, if the transformation fails it
    # returns a default value
    try:
        return int(value)
    except (TypeError, ValueError):
        return default_return


def convert_none_to_bool(value: Union[str, bool], default_return: bool) -> bool:
    # Converts the string 'none' to false else just returns the bool if the
    # passed string represents a bool. If not successful it returns the
    # default_return
    try:
        str_val = str(value).lower()
        if str_val in ['none', 'false']:
            return False
        elif str_val in ['true']:
            return True
        else:
            return default_return
    except (TypeError, ValueError):
        return default_return


def str_to_bool(string: str) -> bool:
    return string.lower() in ['true', 'yes']


def str_to_bool_strict(value: str, default_return: Any) -> Any:
    """
    This function returns True or False strictly if value.lower() == 'true'
    or 'false' respectively. Otherwise, it will return default_return
    :param value: The value to consider
    :param default_return: What to return if 'true' or 'false' cannot be matched
    :return: True if value.lower() == 'true'
             False if value.lower() == 'false'
             default_return otherwise
    """
    value_lower = value.lower()
    if value_lower == 'false':
        return False
    elif value_lower == 'true':
        return True
    else:
        return default_return


def is_mutable(data: Any) -> bool:
    return isinstance(data, MUTABLE_TYPES)
