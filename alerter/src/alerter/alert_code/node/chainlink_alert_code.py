from ..alert_code import AlertCode


class ChainlinkNodeAlertCode(AlertCode):
    NoChangeInHeightAlert = 'cl_node_alert_1'
    BlockHeightUpdatedAlert = 'cl_node_alert_2'
    HeadsInQueueIncreasedAboveThresholdAlert = 'cl_node_alert_3'
    HeadsInQueueDecreasedBelowThresholdAlert = 'cl_node_alert_4'
    NoChangeInTotalHeadersReceivedIncreasedAboveThresholdAlert = \
        'cl_node_alert_5'
    NoChangeInTotalHeadersReceivedDecreasedBelowThresholdAlert = \
        'cl_node_alert_6'
    DroppedBlockHeadersIncreasedAboveThresholdAlert = 'cl_node_alert_7'
    DroppedBlockHeadersDecreasedBelowThresholdAlert = 'cl_node_alert_8'
    MaxUnconfirmedBlocksIncreasedAboveThresholdAlert = 'cl_node_alert_9'
    MaxUnconfirmedBlocksDecreasedBelowThresholdAlert = 'cl_node_alert_10'
    ChangeInSourceNodeAlert = 'cl_node_alert_11'
    GasBumpIncreasedOverNodeGasPriceLimitAlert = 'cl_node_alert_12'
    NoOfUnconfirmedTxsIncreasedAboveThresholdAlert = 'cl_node_alert_13'
    NoOfUnconfirmedTxsDecreasedBelowThresholdAlert = 'cl_node_alert_14'
    TotalErroredJobRunsIncreasedAboveThresholdAlert = 'cl_node_alert_15'
    TotalErroredJobRunsDecreasedBelowThresholdAlert = 'cl_node_alert_16'
    EthBalanceIncreasedAboveThresholdAlert = 'cl_node_alert_17'
    EthBalanceDecreasedBelowThresholdAlert = 'cl_node_alert_18'
    EthBalanceToppedUpAlert = 'cl_node_alert_19'
    InvalidUrlAlert = 'cl_node_alert_20'
    ValidUrlAlert = 'cl_node_alert_21'
    PrometheusSourceIsDownAlert = 'cl_node_alert_22'
    PrometheusSourceBackUpAgainAlert = 'cl_node_alert_23'
    NodeWentDownAtAlert = 'cl_node_alert_24'
    NodeBackUpAgainAlert = 'cl_node_alert_25'
    NodeStillDownAlert = 'cl_node_alert_26'
    MetricNotFoundErrorAlert = 'cl_node_alert_27'
    MetricFoundAlert = 'cl_node_alert_28'
