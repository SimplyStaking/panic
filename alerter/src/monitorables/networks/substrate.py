from typing import Optional, List, Dict

from schema import Schema, Or

from src.monitorables.networks.network import Network
from src.utils.exceptions import InvalidDictSchemaException


class SubstrateNetwork(Network):
    def __init__(self, parent_id: str, chain_name: str) -> None:
        super().__init__(parent_id, chain_name)

        self._grandpa_stalled = None
        self._public_prop_count = None
        # Even tho this will be a list, None is set by default so that the
        # alerter is aware that this is the initial monitoring round.
        self._active_proposals = None
        self._referendum_count = None
        self._referendums = []

        self._last_monitored_websocket = None

    @property
    def grandpa_stalled(self) -> Optional[bool]:
        return self._grandpa_stalled

    @property
    def public_prop_count(self) -> Optional[int]:
        return self._public_prop_count

    @property
    def active_proposals(self) -> Optional[List]:
        return self._active_proposals

    @property
    def referendum_count(self) -> Optional[int]:
        return self._referendum_count

    @property
    def referendums(self) -> List:
        return self._referendums

    @property
    def last_monitored_websocket(self) -> Optional[float]:
        return self._last_monitored_websocket

    def set_grandpa_stalled(self, new_grandpa_stalled: Optional[bool]):
        self._grandpa_stalled = new_grandpa_stalled

    def set_public_prop_count(self, new_public_prop_count: Optional[int]):
        self._public_prop_count = new_public_prop_count

    @staticmethod
    def _are_new_active_proposals_valid(
            new_active_proposals: Optional[List[Dict]]) -> bool:
        schema = Schema(Or([
            {
                'index': Or(int, None),
                'balance': Or(int, None),
                'image': {
                    'at': Or(int, None),
                    'balance': Or(int, None),
                },
                'imageHash': Or(str, None),
                'proposer': Or(str, None),
                'seconds': Or([str], []),
                'seconded': Or({str: bool}, {})
            }
        ], [], None))
        schema.validate(new_active_proposals)
        return schema.is_valid(new_active_proposals)

    def set_active_proposals(self, new_active_proposals: Optional[List[Dict]]):
        if self._are_new_active_proposals_valid(new_active_proposals):
            self._active_proposals = new_active_proposals
        else:
            raise InvalidDictSchemaException('new_active_proposals')

    def set_referendum_count(self, new_referendum_count: Optional[int]):
        self._referendum_count = new_referendum_count

    @staticmethod
    def _are_new_referendums_valid(new_referendums: List[Dict]) -> bool:
        schema = Schema(Or([
            {
                'index': int,
                'status': Or('finished', 'ongoing'),
                'approved': Or(bool, None),
                'end': Or(int, None),
                'data': Or({
                    'proposalHash': Or(str, None),
                    'threshold': Or(str, None),
                    'delay': Or(int, None),
                    'voteCount': Or(int, None),
                    'voteCountAye': Or(int, None),
                    'voteCountNay': Or(int, None),
                    'isPassing': Or(bool, None),
                    'votes': Or([{
                        'accountId': Or(str, None),
                        'isDelegating': Or(bool, None),
                        'vote': Or(bool, None),
                        'balance': Or(int, None),
                    }], []),
                    'voted': Or({str: bool}, {}),
                }, None)
            }
        ], []))
        schema.validate(new_referendums)
        return schema.is_valid(new_referendums)

    def set_referendums(self, new_referendums: List[Dict]):
        if self._are_new_referendums_valid(new_referendums):
            self._referendums = new_referendums
        else:
            raise InvalidDictSchemaException('new_referendums')

    def set_last_monitored_websocket(
            self, new_last_monitored_websocket: Optional[float]) -> None:
        self._last_monitored_websocket = new_last_monitored_websocket

    def reset(self) -> None:
        self.set_grandpa_stalled(None)
        self.set_public_prop_count(None)
        self.set_active_proposals([])
        self.set_referendum_count(None)
        self.set_referendums([])
        self.set_last_monitored_websocket(None)
