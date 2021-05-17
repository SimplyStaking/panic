
from src.monitorables.nodes.node import Node


class ChainlinkNode(Node):
    def __init__(self, node_name: str, node_id: str, parent_id: str) -> None:
        super().__init__(node_name, node_id, parent_id)

        # TODO: Need to put last_source_used with the metrics since it will be
        #     : used to alert on source change.

    def reset(self) -> None:
        """
        This method resets all metrics to their initial state
        :return: None
        """
        pass
