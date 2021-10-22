from datetime import datetime
from typing import Optional, List

from src.monitorables.nodes.node import Node


class EVMNode(Node):
    def __init__(self, node_name: str, node_id: str, parent_id: str) -> None:
        super().__init__(node_name, node_id, parent_id)

        # Metrics
        self._went_down_at = None
        self._current_height = None
        self._syncing = None
        # This stores the timestamp of the last successful monitoring round.
        self._last_monitored = None

    @property
    def is_down(self) -> bool:
        return self._went_down_at is not None

    @property
    def went_down_at(self) -> Optional[float]:
        return self._went_down_at

    @property
    def current_height(self) -> Optional[int]:
        return self._current_height

    @property
    def syncing(self) -> Optional[bool]:
        return self._syncing

    @property
    def last_monitored(self) -> Optional[float]:
        return self._last_monitored

    def set_went_down_at(self, went_down_at: Optional[float]) -> None:
        self._went_down_at = went_down_at

    def set_as_down(self, downtime: Optional[float]) -> None:
        if downtime is None:
            self.set_went_down_at(datetime.now().timestamp())
        else:
            self.set_went_down_at(downtime)

    def set_as_up(self) -> None:
        self.set_went_down_at(None)

    def set_current_height(self, current_height: Optional[int]) -> None:
        self._current_height = current_height

    def set_last_monitored(self, last_monitored: Optional[float]) -> None:
        self._last_monitored = last_monitored

    def set_syncing(self, syncing: Optional[bool]) -> None:
        self._syncing = syncing

    @staticmethod
    def get_int_metric_attributes() -> List[str]:
        """
        :return: A list of all variable names representing integer metrics.
        """
        return ['current_height']

    @staticmethod
    def get_float_metric_attributes() -> List[str]:
        """
        :return: A list of all variable names representing float metrics.
        """
        return ['went_down_at', 'last_monitored']

    @staticmethod
    def get_bool_metric_attributes() -> List[str]:
        """
        :return: A list of all variable names representing bool metrics.
        """
        return ['syncing']

    def reset(self) -> None:
        self.set_went_down_at(None)
        self.set_current_height(None)
        self.set_syncing(None)
        self.set_last_monitored(None)
