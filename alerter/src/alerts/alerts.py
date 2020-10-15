from datetime import datetime
from enum import Enum


# TODO these are imported alerts from PANIC Oasis
_ALERT_ID = 0


def _next_id():
    global _ALERT_ID
    _ALERT_ID += 1
    return _ALERT_ID


class SeverityCode(Enum):
    INFO = 1
    WARNING = 2
    CRITICAL = 3
    ERROR = 4


class AlertCode(Enum):
    ExperiencingDelaysAlert = _next_id(),
    CannotAccessNodeAlert = _next_id(),
    StillCannotAccessNodeAlert = _next_id(),
    NowAccessibleAlert = _next_id(),
    CouldNotFindLiveNodeConnectedToApiServerAlert = _next_id(),
    CouldNotFindLiveArchiveNodeConnectedToApiServerAlert = _next_id(),
    FoundLiveArchiveNodeAgainAlert = _next_id(),
    NodeWasNotConnectedToApiServerAlert = _next_id(),
    NodeConnectedToApiServerAgainAlert = _next_id(),
    NodeInaccessibleDuringStartup = _next_id(),
    BondedBalanceIncreasedAlert = _next_id(),
    BondedBalanceDecreasedAlert = _next_id(),
    BondedBalanceIncreasedByAlert = _next_id(),
    BondedBalanceDecreasedByAlert = _next_id(),
    PeersIncreasedAlert = _next_id(),
    PeersIncreasedOutsideDangerRangeAlert = _next_id(),
    PeersIncreasedOutsideSafeRangeAlert = _next_id(),
    PeersDecreasedAlert = _next_id(),
    IsSyncingAlert = _next_id(),
    IsNoLongerSyncingAlert = _next_id(),
    ValidatorIsNotActiveAlert = _next_id(),
    ValidatorIsNowActiveAlert = _next_id(),
    NodeFinalizedBlockHeightDidNotChangeInAlert = _next_id(),
    NodeFinalizedBlockHeightHasNowBeenUpdatedAlert = _next_id(),
    ProblemWhenDialingNumberAlert = _next_id(),
    ProblemWhenCheckingIfCallsAreSnoozedAlert = _next_id(),
    NewGitHubReleaseAlert = _next_id(),
    CannotAccessGitHubPageAlert = _next_id(),
    RepoInaccessibleDuringStartup = _next_id(),
    AlerterAliveAlert = _next_id(),
    ApiIsUpAgainAlert = _next_id(),
    ApiIsDownAlert = _next_id(),
    TerminatedDueToExceptionAlert = _next_id(),
    TerminatedDueToFatalExceptionAlert = _next_id(),
    ProblemWithTelegramBot = _next_id(),
    NodeIsNotAnArchiveNodeAlert = _next_id(),
    ProblemWithMongo = _next_id(),
    TestAlert = _next_id(),
    VotingPowerIncreasedAlert = _next_id(),
    VotingPowerDecreasedAlert = _next_id(),
    VotingPowerIncreasedByAlert = _next_id(),
    VotingPowerDecreasedByAlert = _next_id(),
    MissedBlocksAlert = _next_id(),
    TimedMissedBlocksAlert = _next_id(),
    NoLongerMissingBlocksAlert = _next_id(),
    SlashedAlert = _next_id(),
    TokensBurnedAlert = _next_id(),
    TokensTransferedToAlert = _next_id(),
    TokensTransferedFromAlert = _next_id(),
    EscrowAddEventSelfOwner = _next_id(),
    EscrowAddEventSelfEscrow = _next_id(),
    EscrowReclaimEventSelfOwner = _next_id(),
    EscrowReclaimEventSelfEscrow = _next_id(),
    UnknownEventFound = _next_id(),
    DebondingBalanceIncreasedAlert = _next_id(),
    DebondingBalanceDecreasedAlert = _next_id(),
    DebondingBalanceIncreasedByAlert = _next_id(),
    DebondingBalanceDecreasedByAlert = _next_id(),
    SharesBalanceIncreasedAlert = _next_id(),
    SharesBalanceDecreasedAlert = _next_id(),
    SharesBalanceIncreasedByAlert = _next_id(),
    SharesBalanceDecreasedByAlert = _next_id(),
    NewProcessCPUSecondsTotalAlert = _next_id(),
    MemoryUsageIncreasedAlert = _next_id(),
    MemoryUsageDecreasedAlert = _next_id(),
    MemoryUsageIncreasedInsideDangerRangeAlert = _next_id(),
    MemoryUsageIncreasedInsideWarningRangeAlert = _next_id(),
    NewVirtualMemoryUsageAlert = _next_id(),
    OpenFileDescriptorsIncreasedAlert = _next_id(),
    OpenFileDescriptorsDecreasedAlert = _next_id(),
    OpenFileDescriptorsIncreasedInsideDangerRangeAlert = _next_id(),
    OpenFileDescriptorsIncreasedInsideWarningRangeAlert = _next_id(),
    SystemCPUUsageIncreasedAlert = _next_id(),
    SystemCPUUsageDecreasedAlert = _next_id(),
    SystemCPUUsageIncreasedInsideDangerRangeAlert = _next_id(),
    SystemCPUUsageIncreasedInsideWarningRangeAlert = _next_id(),
    SystemRAMUsageIncreasedAlert = _next_id(),
    SystemRAMUsageDecreasedAlert = _next_id(),
    SystemRAMUsageIncreasedInsideDangerRangeAlert = _next_id(),
    SystemRAMUsageIncreasedInsideWarningRangeAlert = _next_id(),
    SystemStorageUsageIncreasedAlert = _next_id(),
    SystemStorageUsageDecreasedAlert = _next_id(),
    SystemStorageUsageIncreasedInsideDangerRangeAlert = _next_id(),
    SystemStorageUsageIncreasedInsideWarningRangeAlert = _next_id(),


class Alert:

    def __init__(self, alert_code: AlertCode, message: str) -> None:
        self._alert_code = alert_code
        self._message = message

    @property
    def alert_code(self) -> AlertCode:
        return self._alert_code

    @property
    def message(self) -> str:
        return self._message

    def __str__(self) -> str:
        return self.message


class ExperiencingDelaysAlert(Alert):

    def __init__(self, node: str) -> None:
        super().__init__(
            AlertCode.ExperiencingDelaysAlert,
            'Experiencing delays when trying to access {}.'.format(node))


class FoundLiveArchiveNodeAgainAlert(Alert):

    def __init__(self, monitor: str) -> None:
        super().__init__(
            AlertCode.FoundLiveArchiveNodeAgainAlert,
            '{} found an archive node. This means that archive monitoring '
            '(which includes slashing) is now enabled.'.format(monitor))


class NodeWasNotConnectedToApiServerAlert(Alert):

    def __init__(self, node_name: str) -> None:
        super().__init__(
            AlertCode.NodeWasNotConnectedToApiServerAlert,
            'Node {} was not connected with the API server. Please add the '
            'node to the API server nodes config and restart the API server.'
            ''.format(node_name))


class NodeConnectedToApiServerAgainAlert(Alert):

    def __init__(self, node_name: str) -> None:
        super().__init__(
            AlertCode.NodeConnectedToApiServerAgainAlert,
            'Node {} was connected with the API server again.'
            ''.format(node_name))


class CannotAccessNodeAlert(Alert):

    def __init__(self, node: str) -> None:
        super().__init__(
            AlertCode.CannotAccessNodeAlert,
            'I cannot access {}.'.format(node))


class StillCannotAccessNodeAlert(Alert):

    def __init__(self, node: str, went_down_at: datetime,
                 downtime: str) -> None:
        super().__init__(
            AlertCode.StillCannotAccessNodeAlert,
            'I still cannot access {}. Node became inaccessible at {} '
            'and has been inaccessible for (at most) {}.'.format(
                node, went_down_at, downtime))


class NowAccessibleAlert(Alert):

    def __init__(self, node: str, went_down_at: datetime,
                 downtime: str) -> None:
        super().__init__(
            AlertCode.NowAccessibleAlert,
            '{} is now accessible. Node became inaccessible '
            'at {} and was inaccessible for (at most) {}.'
            ''.format(node, went_down_at, downtime))


class CouldNotFindLiveNodeConnectedToApiServerAlert(Alert):

    def __init__(self, monitor: str) -> None:
        super().__init__(
            AlertCode.CouldNotFindLiveNodeConnectedToApiServerAlert,
            '{} could not find a live node connected to the API '
            'Server to use as a data source.'.format(monitor))


class CouldNotFindLiveArchiveNodeConnectedToApiServerAlert(Alert):

    def __init__(self, monitor: str) -> None:
        super().__init__(
            AlertCode.CouldNotFindLiveArchiveNodeConnectedToApiServerAlert,
            '{} could not find a live archive node connected to the API '
            'Server. Slashing alerts will now be disabled temporarily as these '
            'require data from previous blocks. Other functionality will '
            'continue running normally.'.format(monitor))


class NodeInaccessibleDuringStartup(Alert):

    def __init__(self, node: str) -> None:
        super().__init__(
            AlertCode.NodeInaccessibleDuringStartup,
            'Node {} was not accessible during PANIC startup. {} will NOT be '
            'monitored until it is accessible and PANIC restarted afterwards. '
            'Some features of PANIC might be affected.'.format(node, node))


class BondedBalanceIncreasedAlert(Alert):

    def __init__(self, node: str, old_balance: float, new_balance: float) \
            -> None:
        super().__init__(
            AlertCode.BondedBalanceIncreasedAlert,
            '{} total bonded balance INCREASED from {} to {}.'.format(
                node, old_balance, new_balance))


class BondedBalanceDecreasedAlert(Alert):

    def __init__(self, node: str, old_balance: float, new_balance: float) \
            -> None:
        super().__init__(
            AlertCode.BondedBalanceDecreasedAlert,
            '{} total bonded balance DECREASED from {} to {}.'.format(
                node, old_balance, new_balance))


class BondedBalanceIncreasedByAlert(Alert):

    def __init__(self, node: str, old_balance: float, new_balance: float) \
            -> None:
        change = round(new_balance - old_balance, 3)
        super().__init__(
            AlertCode.BondedBalanceIncreasedByAlert,
            '{} total bonded balance INCREASED by {} from {} to {}.'.format(
                node, change, old_balance, new_balance))


class BondedBalanceDecreasedByAlert(Alert):

    def __init__(self, node: str, old_balance: float, new_balance: float) \
            -> None:
        change = round(old_balance - new_balance, 3)
        super().__init__(
            AlertCode.BondedBalanceDecreasedByAlert,
            '{} total bonded balance DECREASED by {} from {} to {}.'.format(
                node, change, old_balance, new_balance))


class PeersIncreasedAlert(Alert):

    def __init__(self, node: str, old_peers: int, new_peers: int) -> None:
        super().__init__(
            AlertCode.PeersIncreasedAlert,
            '{} peers INCREASED from {} to {}.'.format(
                node, old_peers, new_peers))


class PeersIncreasedOutsideDangerRangeAlert(Alert):

    def __init__(self, node: str, danger: int) -> None:
        super().__init__(
            AlertCode.PeersIncreasedOutsideDangerRangeAlert,
            '{} peers INCREASED to more than {} peers. No further peer change '
            'alerts will be sent unless the number of peers goes below {}.'
            ''.format(node, danger, danger))


class PeersIncreasedOutsideSafeRangeAlert(Alert):

    def __init__(self, node: str, safe: int) -> None:
        super().__init__(
            AlertCode.PeersIncreasedOutsideSafeRangeAlert,
            '{} peers INCREASED to more than {} peers. No further peer change'
            ' alerts will be sent unless the number of peers goes below {}.'
            ''.format(node, safe, safe))


class PeersDecreasedAlert(Alert):

    def __init__(self, node: str, old_peers: int, new_peers: int) -> None:
        super().__init__(
            AlertCode.PeersDecreasedAlert,
            '{} peers DECREASED from {} to {}.'.format(
                node, old_peers, new_peers))


class IsSyncingAlert(Alert):

    def __init__(self, node: str) -> None:
        super().__init__(
            AlertCode.IsSyncingAlert,
            '{} is in syncing state.'.format(node))


class IsNoLongerSyncingAlert(Alert):

    def __init__(self, node: str) -> None:
        super().__init__(
            AlertCode.IsNoLongerSyncingAlert,
            '{} is no longer syncing.'.format(node))


class ValidatorIsNotActiveAlert(Alert):
    def __init__(self, node: str) -> None:
        super().__init__(
            AlertCode.ValidatorIsNotActiveAlert,
            '{} was not found in the list of validators.'.format(node))


class ValidatorIsNowActiveAlert(Alert):

    def __init__(self, node: str) -> None:
        super().__init__(
            AlertCode.ValidatorIsNowActiveAlert,
            '{} has been found in the list of validators.'.format(node))


class NodeFinalizedBlockHeightDidNotChangeInAlert(Alert):

    def __init__(self, node: str, time_of_last_update: str) -> None:
        super().__init__(
            AlertCode.NodeFinalizedBlockHeightDidNotChangeInAlert,
            'The finalized block height of node {} was updated at '
            'least {} ago.'.format(node, time_of_last_update))


class NodeFinalizedBlockHeightHasNowBeenUpdatedAlert(Alert):

    def __init__(self, node: str) -> None:
        super().__init__(
            AlertCode.NodeFinalizedBlockHeightHasNowBeenUpdatedAlert,
            'The finalized block height of node {} was updated.'.format(node))


class ProblemWhenDialingNumberAlert(Alert):

    def __init__(self, number: str, exception: Exception) -> None:
        super().__init__(
            AlertCode.ProblemWhenDialingNumberAlert,
            'Problem encountered when dialing {}: {}'.format(number, exception))


class ProblemWhenCheckingIfCallsAreSnoozedAlert(Alert):

    def __init__(self) -> None:
        super().__init__(
            AlertCode.ProblemWhenCheckingIfCallsAreSnoozedAlert,
            'Problem encountered when checking if calls are snoozed. '
            'Calling anyways.')


class NewGitHubReleaseAlert(Alert):

    def __init__(self, release_name: str, repo_name: str) -> None:
        super().__init__(
            AlertCode.NewGitHubReleaseAlert,
            '{} of {} has just been released.'.format(release_name, repo_name))


class CannotAccessGitHubPageAlert(Alert):

    def __init__(self, page: str) -> None:
        super().__init__(
            AlertCode.CannotAccessGitHubPageAlert,
            'I cannot access GitHub page {}.'.format(page))


class RepoInaccessibleDuringStartup(Alert):

    def __init__(self, repo: str) -> None:
        super().__init__(
            AlertCode.RepoInaccessibleDuringStartup,
            'Repo {} was not accessible during PANIC startup. {} will NOT be '
            'monitored until it is accessible and PANIC restarted afterwards. '
            ''.format(repo, repo))


class AlerterAliveAlert(Alert):

    def __init__(self) -> None:
        super().__init__(AlertCode.AlerterAliveAlert, 'Still running.')


class ApiIsUpAgainAlert(Alert):

    def __init__(self, monitor: str) -> None:
        super().__init__(
            AlertCode.ApiIsUpAgainAlert,
            '{} connected with the API Server again.'.format(monitor))


class ApiIsDownAlert(Alert):

    def __init__(self, monitor: str) -> None:
        super().__init__(
            AlertCode.ApiIsDownAlert,
            '{} lost connection with the API Server. Please make '
            'sure that the API Server is running, otherwise the '
            'monitor cannot retrieve data.'.format(monitor))


class TerminatedDueToExceptionAlert(Alert):

    def __init__(self, component: str, exception: Exception) -> None:
        super().__init__(
            AlertCode.TerminatedDueToExceptionAlert,
            '{} terminated due to exception: {}'.format(component, exception))


class TerminatedDueToFatalExceptionAlert(Alert):

    def __init__(self, component: str, exception: Exception) -> None:
        super().__init__(
            AlertCode.TerminatedDueToFatalExceptionAlert,
            '{} terminated due to fatal exception: {}. {} will NOT restart '
            'to prevent spam.'.format(component, exception, component))


class ProblemWithTelegramBot(Alert):

    def __init__(self, description: str) -> None:
        super().__init__(
            AlertCode.ProblemWithTelegramBot,
            'Problem encountered with telegram bot: {}'.format(description))


class NodeIsNotAnArchiveNodeAlert(Alert):

    def __init__(self, monitor: str, node: str) -> None:
        super().__init__(
            AlertCode.NodeIsNotAnArchiveNodeAlert,
            '{} is not an archive node. {} Will try to find another archive '
            'node. When restarting PANIC please make sure that the '
            'user_config_node file is modified accordingly since non archive '
            'nodes only store data from the last 256 blocks.'
            ''.format(monitor, node))


class ProblemWithMongo(Alert):

    def __init__(self, exception: Exception) -> None:
        super().__init__(
            AlertCode.ProblemWithMongo,
            'Problem encountered with Mongo: {}'.format(exception))


class VotingPowerIncreasedAlert(Alert):

    def __init__(self, node: str, old_power: int, new_power: int) -> None:
        super().__init__(
            AlertCode.VotingPowerIncreasedAlert,
            '{} voting power INCREASED from {} to {}.'.format(
                node, old_power, new_power))


class VotingPowerDecreasedAlert(Alert):

    def __init__(self, node: str, old_power: int, new_power: int) -> None:
        super().__init__(
            AlertCode.VotingPowerDecreasedAlert,
            '{} voting power DECREASED from {} to {}.'.format(
                node, old_power, new_power))


class VotingPowerIncreasedByAlert(Alert):

    def __init__(self, node: str, old_power: int, new_power: int) -> None:
        change = new_power - old_power
        super().__init__(
            AlertCode.VotingPowerIncreasedByAlert,
            '{} voting power INCREASED by {} from {} to {}.'.format(
                node, change, old_power, new_power))


class VotingPowerDecreasedByAlert(Alert):

    def __init__(self, node: str, old_power: int, new_power: int) -> None:
        change = old_power - new_power
        super().__init__(
            AlertCode.VotingPowerDecreasedByAlert,
            '{} voting power DECREASED by {} from {} to {}.'.format(
                node, change, old_power, new_power))


class MissedBlocksAlert(Alert):

    def __init__(self, node: str, blocks: int, height: int,
                 missing_validators: int) -> None:
        super().__init__(
            AlertCode.MissedBlocksAlert,
            '{} missed {} blocks in a row (height: {}, total validators '
            'missing: {}).'.format(node, blocks, height, missing_validators))


class TimedMissedBlocksAlert(Alert):

    def __init__(self, node: str, blocks: int, time_interval: str,
                 height: int, missing_validators: int) -> None:
        super().__init__(
            AlertCode.TimedMissedBlocksAlert,
            '{} missed {} blocks in time interval {} (height: {}, '
            'total validators missing: {}).'.format(
                node, blocks, time_interval, height, missing_validators))


class NoLongerMissingBlocksAlert(Alert):

    def __init__(self, node: str, consecutive_blocks: int) -> None:
        super().__init__(
            AlertCode.NoLongerMissingBlocksAlert,
            '{} is no longer missing blocks (Total missed in a row: {}).'
            ''.format(node, consecutive_blocks))


class SlashedAlert(Alert):

    def __init__(self, node: str, tokens: int, height: int) -> None:
        super().__init__(
            AlertCode.SlashedAlert,
            '{} got slashed {} tokens at height: {} .'.format(node, tokens,
                                                              height))


class TokensBurnedAlert(Alert):

    def __init__(self, node: str, tokens: int, height: int) -> None:
        super().__init__(
            AlertCode.TokensBurnedAlert,
            '{} got burned {} tokens at height: {} .'.format(node, tokens,
                                                             height))


class TokensTransferedToAlert(Alert):

    def __init__(self, node: str, tokens: int, height: int, address: str) \
            -> None:
        super().__init__(
            AlertCode.TokensTransferedToAlert,
            '{} transfered {} tokens to {} at height: {} .'.format(node,
                                                                   tokens,
                                                                   address,
                                                                   height))


class TokensTransferedFromAlert(Alert):

    def __init__(self, node: str, tokens: int, height: int, address: str) \
            -> None:
        super().__init__(
            AlertCode.TokensTransferedFromAlert,
            '{} transfered {} tokens from {} at height: {} .'.format(node,
                                                                     tokens,
                                                                     address,
                                                                     height))


class EscrowAddEventSelfOwner(Alert):

    def __init__(self, node: str, tokens: int, height: int, address: str) \
            -> None:
        super().__init__(
            AlertCode.EscrowAddEventSelfOwner,
            '{} added {} tokens to {} at height: {} .'.format(node, tokens,
                                                              address, height))


class EscrowAddEventSelfEscrow(Alert):

    def __init__(self, node: str, tokens: int, height: int, address: str) \
            -> None:
        super().__init__(
            AlertCode.EscrowAddEventSelfEscrow,
            '{} tokens were added from {} to {} at height {} .'.format(
                tokens, address, node, height))


class EscrowReclaimEventSelfOwner(Alert):

    def __init__(self, node: str, tokens: int, height: int, address: str) \
            -> None:
        super().__init__(
            AlertCode.EscrowReclaimEventSelfOwner,
            '{} tokens were reclaimed from {} by {} at height {} .'.format(
                tokens, node, address, height))


class EscrowReclaimEventSelfEscrow(Alert):

    def __init__(self, node: str, tokens: int, height: int, address: str) \
            -> None:
        super().__init__(
            AlertCode.EscrowReclaimEventSelfEscrow,
            '{} tokens were reclaimed from {} by {} at height {} .'.format(
                tokens, address, node, height))


class UnknownEventFound(Alert):

    def __init__(self, node: str, height: int, event: str) -> None:
        super().__init__(
            AlertCode.UnknownEventFound,
            '{} at height {} an unknown event {} was found!'.format(
                node, height, event))


class DebondingBalanceIncreasedAlert(Alert):

    def __init__(self, node: str, old_balance: float, new_balance: float) \
            -> None:
        super().__init__(
            AlertCode.DebondingBalanceIncreasedAlert,
            '{} total debonding balance INCREASED from {} to {}.'.format(
                node, old_balance, new_balance))


class DebondingBalanceDecreasedAlert(Alert):

    def __init__(self, node: str, old_balance: float, new_balance: float) \
            -> None:
        super().__init__(
            AlertCode.DebondingBalanceDecreasedAlert,
            '{} total debonding balance DECREASED from {} to {}.'.format(
                node, old_balance, new_balance))


class DebondingBalanceIncreasedByAlert(Alert):

    def __init__(self, node: str, old_balance: float, new_balance: float) \
            -> None:
        change = round(new_balance - old_balance, 3)
        super().__init__(
            AlertCode.DebondingBalanceIncreasedByAlert,
            '{} total debonding balance INCREASED by {} from {} to {}.'.format(
                node, change, old_balance, new_balance))


class DebondingBalanceDecreasedByAlert(Alert):

    def __init__(self, node: str, old_balance: float, new_balance: float) \
            -> None:
        change = round(old_balance - new_balance, 3)
        super().__init__(
            AlertCode.DebondingBalanceDecreasedByAlert,
            '{} total debonding balance DECREASED by {} from {} to {}.'.format(
                node, change, old_balance, new_balance))


class SharesBalanceIncreasedAlert(Alert):

    def __init__(self, node: str, old_balance: float, new_balance: float) \
            -> None:
        super().__init__(
            AlertCode.SharesBalanceIncreasedAlert,
            '{} total shares balance INCREASED from {} to {}.'.format(
                node, old_balance, new_balance))


class SharesBalanceDecreasedAlert(Alert):

    def __init__(self, node: str, old_balance: float, new_balance: float) \
            -> None:
        super().__init__(
            AlertCode.SharesBalanceDecreasedAlert,
            '{} total shares balance DECREASED from {} to {}.'.format(
                node, old_balance, new_balance))


class SharesBalanceIncreasedByAlert(Alert):

    def __init__(self, node: str, old_balance: float, new_balance: float) \
            -> None:
        change = round(new_balance - old_balance, 3)
        super().__init__(
            AlertCode.SharesBalanceIncreasedByAlert,
            '{} total shares balance INCREASED by {} from {} to {}.'.format(
                node, change, old_balance, new_balance))


class SharesBalanceDecreasedByAlert(Alert):

    def __init__(self, node: str, old_balance: float, new_balance: float) \
            -> None:
        change = round(old_balance - new_balance, 3)
        super().__init__(
            AlertCode.SharesBalanceDecreasedByAlert,
            '{} total shares balance DECREASED by {} from {} to {}.'.format(
                node, change, old_balance, new_balance))


class NewProcessCPUSecondsTotalAlert(Alert):

    def __init__(self, node: str, cpu_seconds: float) -> None:
        super().__init__(
            AlertCode.NewProcessCPUSecondsTotalAlert,
            '{} new process CPU seconds total {}.'.format(
                node, cpu_seconds))


class MemoryUsageIncreasedAlert(Alert):

    def __init__(self, node: str, old_memory: float, new_memory: float) \
            -> None:
        super().__init__(
            AlertCode.MemoryUsageIncreasedAlert,
            '{} memory usage INCREASED from {}% to {}%.'.format(
                node, old_memory, new_memory))


class MemoryUsageDecreasedAlert(Alert):

    def __init__(self, node: str, old_memory: int, new_memory: int) -> None:
        super().__init__(
            AlertCode.MemoryUsageDecreasedAlert,
            '{} memory usage DECREASED from {}% to {}%.'.format(
                node, old_memory, new_memory))


class MemoryUsageIncreasedInsideDangerRangeAlert(Alert):

    def __init__(self, node: str, new_memory: int, danger: int) -> None:
        super().__init__(
            AlertCode.MemoryUsageIncreasedInsideDangerRangeAlert,
            '{} memory usage Increased to {}%. Above the danger boundary {}%.'
            ''.format(node, new_memory, danger))


class MemoryUsageIncreasedInsideWarningRangeAlert(Alert):

    def __init__(self, node: str, new_memory: int, safe: int) -> None:
        super().__init__(
            AlertCode.MemoryUsageIncreasedInsideWarningRangeAlert,
            '{} memory usage Increased to {}%. Above the safe boundary {}%.'
            ''.format(node, new_memory, safe))


class NewVirtualMemoryUsageAlert(Alert):

    def __init__(self, node: str, memory: float) -> None:
        super().__init__(
            AlertCode.NewVirtualMemoryUsageAlert,
            '{} new virtual memory usage {}.'.format(
                node, memory))


class OpenFileDescriptorsIncreasedAlert(Alert):

    def __init__(self, node: str, old_ofds: float, new_ofds: float) \
            -> None:
        super().__init__(
            AlertCode.OpenFileDescriptorsIncreasedAlert,
            '{} open file descriptors INCREASED from {}% to {}%.'.format(
                node, old_ofds, new_ofds))


class OpenFileDescriptorsDecreasedAlert(Alert):

    def __init__(self, node: str, old_ofds: int, new_ofds: int) -> None:
        super().__init__(
            AlertCode.OpenFileDescriptorsDecreasedAlert,
            '{} open file descriptors DECREASED from {}% to {}%.'.format(
                node, old_ofds, new_ofds))


class OpenFileDescriptorsIncreasedInsideDangerRangeAlert(Alert):

    def __init__(self, node: str, new_ofds: int, danger: int) -> None:
        super().__init__(
            AlertCode.OpenFileDescriptorsIncreasedInsideDangerRangeAlert,
            '{} open file descriptors Increased to {}%. Above the danger '
            'boundary {}%.'.format(node, new_ofds, danger))


class OpenFileDescriptorsIncreasedInsideWarningRangeAlert(Alert):

    def __init__(self, node: str, new_ofds: int, safe: int) -> None:
        super().__init__(
            AlertCode.OpenFileDescriptorsIncreasedInsideWarningRangeAlert,
            '{} open file descriptors Increased to {}%. Above the safe '
            'boundary {}%.'.format(node, new_ofds, safe))


class SystemCPUUsageIncreasedAlert(Alert):

    def __init__(self, node: str, old_cpu_usage: float, new_cpu_usage: float) \
            -> None:
        super().__init__(
            AlertCode.SystemCPUUsageIncreasedAlert,
            '{} system CPU usage INCREASED from {}% to {}%.'.format(
                node, old_cpu_usage, new_cpu_usage))


class SystemCPUUsageDecreasedAlert(Alert):

    def __init__(self, node: str, old_cpu_usage: float, new_cpu_usage: float) \
            -> None:
        super().__init__(
            AlertCode.SystemCPUUsageDecreasedAlert,
            '{} system CPU usage DECREASED from {}% to {}%.'.format(
                node, old_cpu_usage, new_cpu_usage))


class SystemCPUUsageIncreasedInsideDangerRangeAlert(Alert):

    def __init__(self, node: str, new_cpu_usage: int, danger: int) -> None:
        super().__init__(
            AlertCode.SystemCPUUsageIncreasedInsideDangerRangeAlert,
            '{} system CPU usage Increased  to {}%. Above the danger boundary '
            '{}%.'.format(node, new_cpu_usage, danger))


class SystemCPUUsageIncreasedInsideWarningRangeAlert(Alert):

    def __init__(self, node: str, new_cpu_usage: int, safe: int) -> None:
        super().__init__(
            AlertCode.SystemCPUUsageIncreasedInsideWarningRangeAlert,
            '{} system CPU usage Increased to {}%. Above the safe boundary {}%.'
            ''.format(node, new_cpu_usage, safe))


class SystemRAMUsageIncreasedAlert(Alert):

    def __init__(self, node: str, old_ram_usage: float, new_ram_usage: float) \
            -> None:
        super().__init__(
            AlertCode.SystemRAMUsageIncreasedAlert,
            '{} system RAM usage INCREASED from {}% to {}%.'.format(
                node, old_ram_usage, new_ram_usage))


class SystemRAMUsageDecreasedAlert(Alert):

    def __init__(self, node: str, old_ram_usage: float, new_ram_usage: float) \
            -> None:
        super().__init__(
            AlertCode.SystemRAMUsageDecreasedAlert,
            '{} system RAM usage DECREASED from {}% to {}%.'.format(
                node, old_ram_usage, new_ram_usage))


class SystemRAMUsageIncreasedInsideDangerRangeAlert(Alert):

    def __init__(self, node: str, new_ram_usage: int, danger: int) -> None:
        super().__init__(
            AlertCode.SystemRAMUsageIncreasedInsideDangerRangeAlert,
            '{} system RAM usage Increased  to {}%. Above the danger boundary '
            '{}%.'.format(node, new_ram_usage, danger))


class SystemRAMUsageIncreasedInsideWarningRangeAlert(Alert):

    def __init__(self, node: str, new_ram_usage: int, safe: int) -> None:
        super().__init__(
            AlertCode.SystemRAMUsageIncreasedInsideWarningRangeAlert,
            '{} system RAM usage Increased to {}%. Above the safe boundary {}%.'
            ''.format(node, new_ram_usage, safe))


class SystemStorageUsageIncreasedAlert(Alert):

    def __init__(self, node: str, old_storage: float, new_storage: float) \
            -> None:
        super().__init__(
            AlertCode.SystemStorageUsageIncreasedAlert,
            '{} system storage usage INCREASED from {}% to {}%.'.format(
                node, old_storage, new_storage))


class SystemStorageUsageDecreasedAlert(Alert):

    def __init__(self, node: str, old_storage: int, new_storage: int) -> None:
        super().__init__(
            AlertCode.SystemStorageUsageDecreasedAlert,
            '{} system storage usage DECREASED from {}% to {}%.'.format(
                node, old_storage, new_storage))


class SystemStorageUsageIncreasedInsideDangerRangeAlert(Alert):

    def __init__(self, node: str, new_storage_usage: int, danger: int) -> None:
        super().__init__(
            AlertCode.SystemStorageUsageIncreasedInsideDangerRangeAlert,
            '{} system storage usage Increased  to {}%. Above the danger '
            'boundary {}%.'.format(node, new_storage_usage, danger))


class SystemStorageUsageIncreasedInsideWarningRangeAlert(Alert):

    def __init__(self, node: str, new_storage_usage: int, safe: int) -> None:
        super().__init__(
            AlertCode.SystemStorageUsageIncreasedInsideWarningRangeAlert,
            '{} system storage usage Increased to {}%. Above the safe boundary '
            '{}%.'.format(node, new_storage_usage, safe))
