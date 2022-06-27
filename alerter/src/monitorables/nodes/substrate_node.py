from datetime import datetime
from typing import Optional, Dict, List

from schema import Schema, Or

from src.monitorables.nodes.node import Node
from src.utils.exceptions import InvalidDictSchemaException


class SubstrateNode(Node):
    def __init__(self, node_name: str, node_id: str, parent_id: str) -> None:
        super().__init__(node_name, node_id, parent_id)

        # Metrics
        self._went_down_at_websocket = None
        self._best_height = None
        self._target_height = None
        self._finalized_height = None
        self._current_session = None
        self._current_era = None
        self._authored_blocks = None
        self._active = None
        self._elected = None
        self._disabled = None
        self._eras_stakers = {
            'total': None,
            'own': None,
            'others': []
        }
        self._sent_heartbeat = None
        self._controller_address = None
        self._history_depth_eras = None
        self._unclaimed_rewards = []
        self._claimed_rewards = []
        self._previous_era_rewards = None
        self._historical = []
        self._token_symbol = None

        # Storing timestamp of the last successful monitoring round
        self._last_monitored_websocket = None

    @property
    def is_down_websocket(self) -> bool:
        return self._went_down_at_websocket is not None

    @property
    def went_down_at_websocket(self) -> Optional[float]:
        return self._went_down_at_websocket

    @property
    def best_height(self) -> Optional[int]:
        return self._best_height

    @property
    def target_height(self) -> Optional[int]:
        return self._target_height

    @property
    def finalized_height(self) -> Optional[int]:
        return self._finalized_height

    @property
    def current_session(self) -> Optional[int]:
        return self._current_session

    @property
    def current_era(self) -> Optional[int]:
        return self._current_era

    @property
    def authored_blocks(self) -> Optional[int]:
        return self._authored_blocks

    @property
    def active(self) -> Optional[bool]:
        return self._active

    @property
    def elected(self) -> Optional[bool]:
        return self._elected

    @property
    def disabled(self) -> Optional[bool]:
        return self._disabled

    @property
    def eras_stakers(self) -> Dict:
        return self._eras_stakers

    @property
    def sent_heartbeat(self) -> Optional[bool]:
        return self._sent_heartbeat

    @property
    def controller_address(self) -> Optional[str]:
        return self._controller_address

    @property
    def history_depth_eras(self) -> Optional[int]:
        return self._history_depth_eras

    @property
    def unclaimed_rewards(self) -> List:
        return self._unclaimed_rewards

    @property
    def claimed_rewards(self) -> List:
        return self._claimed_rewards

    @property
    def previous_era_rewards(self) -> Optional[int]:
        return self._previous_era_rewards

    @property
    def historical(self) -> List:
        return self._historical

    @property
    def token_symbol(self) -> Optional[str]:
        return self._token_symbol

    @property
    def last_monitored_websocket(self) -> Optional[float]:
        return self._last_monitored_websocket

    def set_went_down_at_websocket(
            self, went_down_at_websocket: Optional[float]) -> None:
        self._went_down_at_websocket = went_down_at_websocket

    def set_websocket_as_down(self, downtime: Optional[float]) -> None:
        """
        This function sets the node's websocket interface as down. It sets the
        time that the interface was initially down to the parameter 'downtime'
        if it is not None, otherwise it sets it to the current timestamp.
        :param downtime: downtime timestamp
        :return:
        """
        if downtime is None:
            self.set_went_down_at_websocket(datetime.now().timestamp())
        else:
            self.set_went_down_at_websocket(downtime)

    def set_websocket_as_up(self) -> None:
        """
        This function sets a node's websocket interface as up. A node's
        interface is said to be up if went_down_at_prometheus is None.
        :return: None
        """
        self.set_went_down_at_websocket(None)

    def set_best_height(self, best_height: Optional[int]) -> None:
        self._best_height = best_height

    def set_target_height(self, target_height: Optional[int]) -> None:
        self._target_height = target_height

    def set_finalized_height(self, finalized_height: Optional[int]) -> None:
        self._finalized_height = finalized_height

    def set_current_session(self, current_session: Optional[int]) -> None:
        self._current_session = current_session

    def set_current_era(self, current_era: Optional[int]) -> None:
        self._current_era = current_era

    def set_authored_blocks(self, authored_blocks: Optional[int]) -> None:
        self._authored_blocks = authored_blocks

    def set_active(self, active: Optional[bool]) -> None:
        self._active = active

    def set_elected(self, elected: Optional[bool]) -> None:
        self._elected = elected

    def set_disabled(self, disabled: Optional[bool]) -> None:
        self._disabled = disabled

    @staticmethod
    def _is_new_eras_stakers_valid(new_eras_stakers: Dict) -> bool:
        """
        This function checks whether new_eras_stakers obeys the schema enforced
        on self._eras_stakers.
        :param new_eras_stakers: The dict to check
        :return: True if new_eras_stakers obeys the required schema
                 False otherwise
        """
        schema = Schema(Or({
            'total': Or(int, float, None),
            'own': Or(int, float, None),
            'others': Schema(Or(
                [
                    {
                        'who': str,
                        'value': Or(int, float),
                    }
                ], [])),
        }, {}))
        return schema.is_valid(new_eras_stakers)

    def set_eras_stakers(self, new_eras_stakers: Dict) -> None:
        if self._is_new_eras_stakers_valid(new_eras_stakers):
            self._eras_stakers = new_eras_stakers
        else:
            raise InvalidDictSchemaException('new_eras_stakers')

    def set_sent_heartbeat(self, sent_heartbeat: Optional[bool]) -> None:
        self._sent_heartbeat = sent_heartbeat

    def set_controller_address(self, controller_address: Optional[str]) -> None:
        self._controller_address = controller_address

    def set_history_depth_eras(self, history_depth_eras: Optional[int]) -> None:
        self._history_depth_eras = history_depth_eras

    def set_unclaimed_rewards(self, unclaimed_rewards: List) -> None:
        self._unclaimed_rewards = unclaimed_rewards

    def set_claimed_rewards(self, claimed_rewards: List) -> None:
        self._claimed_rewards = claimed_rewards

    def set_previous_era_rewards(
            self, previous_era_rewards: Optional[int]) -> None:
        self._previous_era_rewards = previous_era_rewards

    def set_historical(self, historical: List) -> None:
        self._historical = historical

    def set_token_symbol(self, new_token_symbol: Optional[str]) -> None:
        self._token_symbol = new_token_symbol

    def set_last_monitored_websocket(
            self, new_last_monitored_websocket: Optional[float]) -> None:
        self._last_monitored_websocket = new_last_monitored_websocket

    def reset(self) -> None:
        """
        This method resets all metrics to their initial state
        :return: None
        """
        self.set_best_height(None)
        self.set_target_height(None)
        self.set_finalized_height(None)
        self.set_current_session(None)
        self.set_current_era(None)
        self.set_authored_blocks(None)
        self.set_active(None)
        self.set_elected(None)
        self.set_disabled(None)
        self.set_eras_stakers({'total': None, 'own': None, 'others': []})
        self.set_sent_heartbeat(None)
        self.set_controller_address(None)
        self.set_history_depth_eras(None)
        self.set_unclaimed_rewards([])
        self.set_claimed_rewards([])
        self.set_previous_era_rewards(None)
        self.set_historical([])
        self.set_token_symbol(None)
