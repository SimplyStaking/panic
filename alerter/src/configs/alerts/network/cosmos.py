from typing import Dict, Any


class CosmosNetworkAlertsConfig:
    def __init__(
            self, parent_id: str, new_proposal: Dict,
            proposal_concluded: Dict) -> None:
        self._parent_id = parent_id
        self._new_proposal = new_proposal
        self._proposal_concluded = proposal_concluded

    def __eq__(self, other: Any) -> bool:
        return self.__dict__ == other.__dict__

    @property
    def parent_id(self) -> str:
        return self._parent_id

    @property
    def new_proposal(self) -> Dict:
        return self._new_proposal

    @property
    def proposal_concluded(self) -> Dict:
        return self._proposal_concluded
