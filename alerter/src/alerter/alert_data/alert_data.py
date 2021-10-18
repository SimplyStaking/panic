from abc import abstractmethod, ABC
from typing import Dict


class AlertData(ABC):
    """
    Define an empty object which will hold the extra data needed for special
    alerts.
    """

    def __init__(self):
        self._alert_data = {}

    @property
    def alert_data(self) -> Dict:
        return self._alert_data

    @abstractmethod
    def set_alert_data(self, *args) -> None:
        """
        This will be used to store the data from the parameters into the
        appropriate dictionary structure.
        """
        pass
