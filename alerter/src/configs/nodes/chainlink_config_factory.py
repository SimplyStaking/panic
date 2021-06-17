from src.configs.nodes.chainlink import ChainlinkNodeConfig


class ChainlinkConfigFactory():
    def __init__(self) -> None:
        self._node_configs = {}

    @property
    def node_configs(self) -> Dict:
        return self._node_configs

    def process_config(self, received_data: Dict) -> None:

    def add_new_config(self, received_data: Dict) -> None:

    def modify_config(self, recieved_data: Dict) -> None:

    def remove_config(self, received_data: Data) -> None:
