from typing import Dict, Any


class ChainlinkContractAlertsConfig:
    def __init__(self, parent_id: str,
                 price_feed_not_observed: Dict,
                 price_feed_deviation: Dict,
                 consensus_failure: Dict) -> None:
        self._parent_id = parent_id
        self._price_feed_not_observed = price_feed_not_observed
        self._price_feed_deviation = price_feed_deviation
        self._consensus_failure = consensus_failure

    def __eq__(self, other: Any) -> bool:
        return self.__dict__ == other.__dict__

    @property
    def parent_id(self) -> str:
        return self._parent_id

    @property
    def price_feed_not_observed(self) -> Dict:
        return self._price_feed_not_observed

    @property
    def price_feed_deviation(self) -> Dict:
        return self._price_feed_deviation

    @property
    def consensus_failure(self) -> Dict:
        return self._consensus_failure
