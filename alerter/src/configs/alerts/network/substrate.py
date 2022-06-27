from typing import Dict, Any


class SubstrateNetworkAlertsConfig:
    def __init__(
            self, parent_id: str, grandpa_is_stalled: Dict, new_proposal: Dict,
            new_referendum: Dict, referendum_concluded: Dict) -> None:
        self._parent_id = parent_id
        self._grandpa_is_stalled = grandpa_is_stalled
        self._new_proposal = new_proposal
        self._new_referendum = new_referendum
        self._referendum_concluded = referendum_concluded

    def __eq__(self, other: Any) -> bool:
        return self.__dict__ == other.__dict__

    @property
    def parent_id(self) -> str:
        return self._parent_id

    @property
    def grandpa_is_stalled(self) -> Dict:
        return self._grandpa_is_stalled

    @property
    def new_proposal(self) -> Dict:
        return self._new_proposal

    @property
    def new_referendum(self) -> Dict:
        return self._new_referendum

    @property
    def referendum_concluded(self) -> Dict:
        return self._referendum_concluded
