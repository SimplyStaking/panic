from ..alert_code import AlertCode


class EVMNodeAlertCode(AlertCode):
    NoChangeInBlockHeight = 'evm_node_alert_1'
    BlockHeightUpdatedAlert = 'evm_node_alert_2'
    BlockHeightDifferenceIncreasedAboveThresholdAlert = 'evm_node_alert_3'
    BlockHeightDifferenceDecreasedBelowThresholdAlert = 'evm_node_alert_4'
    InvalidUrlAlert = 'evm_node_alert_5'
    ValidUrlAlert = 'evm_node_alert_6'
    NodeWentDownAtAlert = 'evm_node_alert_7'
    NodeBackUpAgainAlert = 'evm_node_alert_8'
    NodeStillDownAlert = 'evm_node_alert_9'
