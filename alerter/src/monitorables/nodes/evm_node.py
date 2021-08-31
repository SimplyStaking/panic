from datetime import datetime
from typing import Optional, Dict, List, Union

from schema import Schema, Or

from src.monitorables.nodes.node import Node
from src.utils.exceptions import InvalidDictSchemaException


class EVMNode(Node):
    def __init__(self, node_name: str, node_id: str, parent_id: str) -> None:
        super().__init__(node_name, node_id, parent_id)

        # Metrics
        self._went_down_at = None
        self._current_height = None

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
    def last_monitored(self) -> Optional[float]:
        return self._last_monitored

    @staticmethod
    def get_int_metric_attributes() -> List[str]:
        """
        :return: A list of all variable names representing integer
               : metrics.
        """
        return [
            'current_height',
        ]

    @staticmethod
    def get_float_metric_attributes() -> List[str]:
        """
        :return: A list of all variable names representing float
               : metrics.
        """
        return [
            'went_down_at', 'last_monitored'
        ]

    def get_all_metric_attributes(self) -> List[str]:
        """
        :return: A list of all variable names representing metrics
        """
        int_metric_attributes = \
            self.get_int_metric_attributes()
        float_metric_attributes = \
            self.get_float_metric_attributes()
        return [
            *int_metric_attributes,
            *float_metric_attributes,
        ]

    def get_int_metric_attributes(self) -> List[str]:
        """
        :return: A list of all variable names representing int metrics.
        """
        int_metric_attributes = \
            self.get_int_metric_attributes()
        return [*int_metric_attributes]

    def get_float_metric_attributes(self) -> List[str]:
        """
        :return: A list of all variable names representing float metrics.
        """
        float_metric_attributes = \
            self.get_float_metric_attributes()
        return [*float_metric_attributes]

    def get_all_metric_attributes(self) -> List[str]:
        """
        :return: A list of all variable names representing metrics
        """
        metric_attributes = \
            self.get_all_metric_attributes()
        return [*metric_attributes]

    def set_went_down_at(
            self, went_down_at: Optional[float]) -> None:
        self._went_down_at = went_down_at

    def set_as_down(self, downtime: Optional[float]) -> None:
        """
        This function sets the node's interface as down. It sets the
        time that the interface was initially down to the parameter 'downtime'
        if it is not None, otherwise it sets it to the current timestamp.
        :param downtime:
        :return:
        """
        if downtime is None:
            self.set_went_down_at(datetime.now().timestamp())
        else:
            self.set_went_down_at(downtime)

    def set_as_up(self) -> None:
        """
        This function sets a node's interface as up. A node's
        interface is said to be up if went_down_at is None.
        :return: None
        """
        self.set_went_down_at(None)

    def set_current_height(self, new_height: Optional[int]) -> None:
        self._current_height = new_height

    def set_last_monitored(
            self, new_last_monitored: Optional[float]) -> None:
        self._last_monitored = new_last_monitored

    def reset(self) -> None:
        """
        This method resets all metrics to their initial state
        :return: None
        """
        self.set_went_down_at(None)
        self.set_current_height(None)
        self.set_last_monitored(None)
