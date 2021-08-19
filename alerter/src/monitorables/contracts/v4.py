from typing import Dict, List, Optional

from schema import Schema, Or

from src.monitorables.contracts.contract import Contract


class V4Contract(Contract):
    def __init__(self, address: str) -> None:
        super().__init__(address, 3)
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
                'roundTimestamp': float,
                'answeredInRound': int,
                'nodeSubmission': Or(int, None),
                'nodeObservations': int,
                'noOfTransmitters': int,
            }
        ])
        return schema.is_valid(new_historical_rounds)

    def reset(self) -> None:
        self.set_latest_round(None)
        self.set_latest_answer(None)
        self.set_latest_timestamp(None)
        self.set_answered_in_round(None)
        self.set_historical_rounds([])
        self.set_owed_payment(None)
