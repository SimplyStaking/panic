from datetime import datetime
from typing import Optional, Dict

from schema import Schema, Or

from src.monitorables.nodes.node import Node
from src.utils.constants.cosmos import BondStatus
from src.utils.exceptions import InvalidDictSchemaException


class CosmosNode(Node):
    def __init__(self, node_name: str, node_id: str, parent_id: str) -> None:
        super().__init__(node_name, node_id, parent_id)

        # Metrics
        self._went_down_at_prometheus = None
        self._went_down_at_cosmos_rest = None
        self._went_down_at_tendermint_rpc = None
        self._current_height = None
        self._voting_power = None
        self._is_syncing = None
        self._bond_status = None
        self._jailed = None

        # NOTE: For the two structs below keep in mind that at each monitoring
        # round we will be receiving a list of data from various heights.

        # If slashing occurs in at least one block height, then 'slashed' will
        # be set to True, otherwise, it will be set to False. 'amount_map' is a
        # map from the slashed block heights considered at the last monitoring
        # round to the amount slashed at that block height (We can't store all
        # heights since startup because we may eventually run out of memory).
        # NOTE: Slashed amount might be None as it may not be available.
        self._slashed = {
            'slashed': False,
            'amount_map': {}
        }

        # 'total_count' is a counter representing the total missed blocks since
        # the start. 'missed_heights' represents the missed blocks of the last
        # monitoring round (We cannot store everything because we may eventually
        # run out of memory).
        self._missed_blocks = {
            'total_count': 0,
            'missed_heights': []
        }

        # These store the timestamps of the last successful monitoring round.
        self._last_monitored_prometheus = None
        self._last_monitored_tendermint_rpc = None
        self._last_monitored_cosmos_rest = None

    @property
    def is_down_prometheus(self) -> bool:
        return self._went_down_at_prometheus is not None

    @property
    def went_down_at_prometheus(self) -> Optional[float]:
        return self._went_down_at_prometheus

    @property
    def is_down_cosmos_rest(self) -> bool:
        return self._went_down_at_cosmos_rest is not None

    @property
    def went_down_at_cosmos_rest(self) -> Optional[float]:
        return self._went_down_at_cosmos_rest

    @property
    def is_down_tendermint_rpc(self) -> bool:
        return self._went_down_at_tendermint_rpc is not None

    @property
    def went_down_at_tendermint_rpc(self) -> Optional[float]:
        return self._went_down_at_tendermint_rpc

    @property
    def current_height(self) -> Optional[int]:
        return self._current_height

    @property
    def voting_power(self) -> Optional[int]:
        return self._voting_power

    @property
    def is_syncing(self) -> Optional[bool]:
        return self._is_syncing

    @property
    def bond_status(self) -> Optional[BondStatus]:
        return self._bond_status

    @property
    def jailed(self) -> Optional[bool]:
        return self._jailed

    @property
    def slashed(self) -> Dict:
        return self._slashed

    @property
    def missed_blocks(self) -> Dict:
        return self._missed_blocks

    @property
    def last_monitored_prometheus(self) -> Optional[float]:
        return self._last_monitored_prometheus

    @property
    def last_monitored_tendermint_rpc(self) -> Optional[float]:
        return self._last_monitored_tendermint_rpc

    @property
    def last_monitored_cosmos_rest(self) -> Optional[float]:
        return self._last_monitored_cosmos_rest

    def set_went_down_at_prometheus(
            self, went_down_at_prometheus: Optional[float]) -> None:
        self._went_down_at_prometheus = went_down_at_prometheus

    def set_prometheus_as_down(self, downtime: Optional[float]) -> None:
        """
        This function sets the node's prometheus interface as down. It sets the
        time that the interface was initially down to the parameter 'downtime'
        if it is not None, otherwise it sets it to the current timestamp.
        :param downtime: downtime timestamp
        :return:
        """
        if downtime is None:
            self.set_went_down_at_prometheus(datetime.now().timestamp())
        else:
            self.set_went_down_at_prometheus(downtime)

    def set_prometheus_as_up(self) -> None:
        """
        This function sets a node's prometheus interface as up. A node's
        interface is said to be up if went_down_at_prometheus is None.
        :return: None
        """
        self.set_went_down_at_prometheus(None)

    def set_went_down_at_cosmos_rest(
            self, went_down_at_cosmos_rest: Optional[float]) -> None:
        self._went_down_at_cosmos_rest = went_down_at_cosmos_rest

    def set_cosmos_rest_as_down(self, downtime: Optional[float]) -> None:
        """
        This function sets the node's cosmos-rest interface as down. It sets the
        time that the interface was initially down to the parameter 'downtime'
        if it is not None, otherwise it sets it to the current timestamp.
        :param downtime: downtime timestamp
        :return:
        """
        if downtime is None:
            self.set_went_down_at_cosmos_rest(datetime.now().timestamp())
        else:
            self.set_went_down_at_cosmos_rest(downtime)

    def set_cosmos_rest_as_up(self) -> None:
        """
        This function sets a node's cosmos-rest interface as up. A node's
        interface is said to be up if went_down_at_cosmos_rest is None.
        :return: None
        """
        self.set_went_down_at_cosmos_rest(None)

    def set_went_down_at_tendermint_rpc(
            self, went_down_at_tendermint_rpc: Optional[float]) -> None:
        self._went_down_at_tendermint_rpc = went_down_at_tendermint_rpc

    def set_tendermint_rpc_as_down(self, downtime: Optional[float]) -> None:
        """
        This function sets the node's tendermint-rpc interface as down. It sets
        the time that the interface was initially down to the parameter
        'downtime' if it is not None, otherwise it sets it to the current
        timestamp.
        :param downtime: downtime timestamp
        :return:
        """
        if downtime is None:
            self.set_went_down_at_tendermint_rpc(datetime.now().timestamp())
        else:
            self.set_went_down_at_tendermint_rpc(downtime)

    def set_tendermint_rpc_as_up(self) -> None:
        """
        This function sets a node's tendermint-rpc interface as up. A node's
        interface is said to be up if went_down_at_tendermint_rpc is None.
        :return: None
        """
        self.set_went_down_at_tendermint_rpc(None)

    def set_current_height(self, new_height: Optional[int]) -> None:
        self._current_height = new_height

    def set_voting_power(self, new_voting_power: Optional[int]) -> None:
        self._voting_power = new_voting_power

    def set_is_syncing(self, new_is_syncing: Optional[bool]) -> None:
        self._is_syncing = new_is_syncing

    def set_bond_status(self, new_bond_status: Optional[BondStatus]) -> None:
        self._bond_status = new_bond_status

    def set_jailed(self, new_jailed: Optional[bool]) -> None:
        self._jailed = new_jailed

    @staticmethod
    def _is_new_slashed_valid(new_slashed: Dict) -> bool:
        """
        This function checks whether new_slashed obeys the schema enforced on
        self._slashed.
        :param new_slashed: The dict to check
        :return: True if new_slashed obeys the required schema
                 False otherwise
        """
        schema = Schema(Or({
            'slashed': bool,
            'amount_map': Schema(Or({str: Or(float, None)}, {})),
        }, {}))
        return schema.is_valid(new_slashed)

    def set_slashed(self, new_slashed: Dict) -> None:
        """
        This method sets the value of self._slashed to new_slashed if
        new_slashed obeys the required schema. Otherwise, this function will
        raise an InvalidDictSchemaException.
        :param new_slashed: The new slashed value
        :return: None
        """
        if self._is_new_slashed_valid(new_slashed):
            self._slashed = new_slashed
        else:
            raise InvalidDictSchemaException('new_slashed')

    @staticmethod
    def _is_new_missed_blocks_valid(new_missed_blocks: Dict) -> bool:
        """
        This function checks whether new_missed_blocks obeys the schema enforced
        on self._missed_blocks.
        :param new_missed_blocks: The dict to check
        :return: True if new_missed_blocks obeys the required schema
                 False otherwise
        """
        schema = Schema(Or({
            'total_count': int,
            'missed_heights': Schema([int]),
        }, {}))
        return schema.is_valid(new_missed_blocks)

    def set_missed_blocks(self, new_missed_blocks: Dict) -> None:
        """
        This method sets the value of self._missed_blocks to new_missed_blocks
        if new_missed_blocks obeys the required schema. Otherwise, this function
        will raise an InvalidDictSchemaException.
        :param new_missed_blocks: The new missed_blocks value
        :return: None
        """
        if self._is_new_missed_blocks_valid(new_missed_blocks):
            self._missed_blocks = new_missed_blocks
        else:
            raise InvalidDictSchemaException('new_missed_blocks')

    def set_last_monitored_prometheus(
            self, new_last_monitored_prometheus: Optional[float]) -> None:
        self._last_monitored_prometheus = new_last_monitored_prometheus

    def set_last_monitored_tendermint_rpc(
            self, new_last_monitored_tendermint_rpc: Optional[float]) -> None:
        self._last_monitored_tendermint_rpc = new_last_monitored_tendermint_rpc

    def set_last_monitored_cosmos_rest(
            self, new_last_monitored_cosmos_rest: Optional[float]) -> None:
        self._last_monitored_cosmos_rest = new_last_monitored_cosmos_rest

    def reset(self) -> None:
        """
        This method resets all metrics to their initial state
        :return: None
        """
        self.set_went_down_at_prometheus(None)
        self.set_went_down_at_cosmos_rest(None)
        self.set_went_down_at_tendermint_rpc(None)
        self.set_current_height(None)
        self.set_voting_power(None)
        self.set_is_syncing(None)
        self.set_bond_status(None)
        self.set_jailed(None)
        self.set_slashed({'slashed': False, 'amount_map': {}})
        self.set_missed_blocks({'total_count': 0, 'missed_heights': []})
        self.set_last_monitored_prometheus(None)
        self.set_last_monitored_cosmos_rest(None)
        self.set_last_monitored_tendermint_rpc(None)
