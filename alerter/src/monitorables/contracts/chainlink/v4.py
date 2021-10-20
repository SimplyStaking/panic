from typing import Dict, List, Optional

from schema import Schema, Or

from src.monitorables.contracts.chainlink.contract import ChainlinkContract


class V4ChainlinkContract(ChainlinkContract):
    def __init__(self, proxy_address: str, aggregator_address: str,
                 parent_id: str, node_id: str) -> None:
        super().__init__(proxy_address, aggregator_address, 4, parent_id,
                         node_id)
        self._owed_payment = None

    @property
    def owed_payment(self) -> Optional[int]:
        return self._owed_payment

    def set_owed_payment(self, owed_payment: Optional[int]) -> None:
        self._owed_payment = owed_payment

    def historical_rounds_valid(self,
                                new_historical_rounds: List[Dict]) -> bool:
        """
        This function returns true if the new historical_rounds value obeys the
        required schema and false otherwise
        :param new_historical_rounds: The new historical_rounds value to be set
        :return: True if schema obeyed
               : False otherwise
        """
        schema = Schema([
            {
                'roundId': int,
                'roundAnswer': int,
                'roundTimestamp': int,
                'answeredInRound': int,
                'nodeSubmission': Or(int, None),
                'noOfObservations': int,
                'noOfTransmitters': int,
                'deviation': Or(float, None),
            }
        ])
        return schema.is_valid(new_historical_rounds)

    @staticmethod
    def get_int_metric_attributes() -> List[str]:
        """
        :return: A list of all variable names representing integer metrics.
        """
        return ['_latest_round', '_latest_answer', '_answered_in_round',
                '_owed_payment', '_last_round_observed']

    @staticmethod
    def get_float_metric_attributes() -> List[str]:
        """
        :return: A list of all variable names representing float metrics.
        """
        return ['_latest_timestamp', '_last_monitored']

    @staticmethod
    def get_list_metric_attributes() -> List[str]:
        """
        :return: A list of all variable names representing dict metrics.
        """
        return ['_historical_rounds']

    def reset(self) -> None:
        self.set_latest_round(None)
        self.set_latest_answer(None)
        self.set_latest_timestamp(None)
        self.set_answered_in_round(None)
        self.set_historical_rounds([])
        self.set_owed_payment(None)
        self.set_last_monitored(None)
        self.set_last_round_observed(None)
