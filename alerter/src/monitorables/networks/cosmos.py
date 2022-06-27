from typing import Optional, List, Dict

from schema import Schema, Or

from src.monitorables.networks.network import Network
from src.utils.exceptions import InvalidDictSchemaException


class CosmosNetwork(Network):
    def __init__(self, parent_id: str, chain_name: str) -> None:
        super().__init__(parent_id, chain_name)

        self._proposals = []

        self._last_monitored_cosmos_rest = None

    @property
    def proposals(self) -> List:
        return self._proposals

    @property
    def last_monitored_cosmos_rest(self) -> float:
        return self._last_monitored_cosmos_rest

    @staticmethod
    def _are_new_proposals_valid(new_proposals: List[Dict]) -> bool:
        schema = Schema(Or([
            {
                'proposal_id': Or(int, None),
                'title': str,
                'description': str,
                'status': str,
                'final_tally_result': {
                    'yes': Or(float, None),
                    'abstain': Or(float, None),
                    'no': Or(float, None),
                    'no_with_veto': Or(float, None),
                },
                'submit_time': float,
                'deposit_end_time': float,
                'total_deposit': [
                    {
                        'denom': str,
                        'amount': Or(float, None),
                    }
                ],
                'voting_start_time': float,
                'voting_end_time': float,
            }
        ], []))
        schema.validate(new_proposals)
        return schema.is_valid(new_proposals)

    def set_proposals(self, new_proposals: List[Dict]):
        if self._are_new_proposals_valid(new_proposals):
            self._proposals = new_proposals
        else:
            raise InvalidDictSchemaException('new_proposals')

    def set_last_monitored_cosmos_rest(
            self, new_last_monitored_cosmos_rest: Optional[float]) -> None:
        self._last_monitored_cosmos_rest = new_last_monitored_cosmos_rest

    def reset(self) -> None:
        self.set_proposals([])
        self.set_last_monitored_cosmos_rest(None)
