from src.configs.nodes.chainlink import ChainlinkNodeConfig


class ChainlinkTestNodes:
    def __init__(self) -> None:
        self._node_1 = ChainlinkNodeConfig(
            'node_id_1', 'parent_id_1', 'node_name_1', True, True,
            ['prom_url_1', 'prom_url_2', 'prom_url_3'])
        self._node_2 = ChainlinkNodeConfig(
            'node_id_2', 'parent_id_2', 'node_name_2', True, True,
            ['prom_url_4', 'prom_url_5', 'prom_url_6'])

    @property
    def node_1(self) -> ChainlinkNodeConfig:
        return self._node_1

    @property
    def node_2(self) -> ChainlinkNodeConfig:
        return self._node_2

    def clear_attributes(self) -> None:
        """
        This function sets all attributes to None. It is mostly used for
        testing.
        """
        self._node_1 = None
        self._node_2 = None
