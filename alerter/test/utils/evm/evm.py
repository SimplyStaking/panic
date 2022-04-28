from src.configs.nodes.evm import EVMNodeConfig


class EVMTestNodes:
    def __init__(self) -> None:
        self._node_1 = EVMNodeConfig('node_id_1', 'parent_id_1', 'node_name_1',
                                     True, 'node_http_url_1')
        self._node_2 = EVMNodeConfig('node_id_2', 'parent_id_2', 'node_name_2',
                                     True, 'node_http_url_2')

    @property
    def node_1(self) -> EVMNodeConfig:
        return self._node_1

    @property
    def node_2(self) -> EVMNodeConfig:
        return self._node_2

    @staticmethod
    def create_custom_node(
            node_id: str, parent_id: str, node_name: str,
            monitor_node: bool, node_http_url: str) -> EVMNodeConfig:
        """
        Given all the required fields to create an EVMNodeConfig instance, this
        function will return an EVMNodeConfig with the custom fields
        :param node_id: The node id
        :param parent_id: The parent id
        :param node_name: The node name
        :param monitor_node: Whether to monitor the node or not
        :param node_http_url: The node's http url
        :return: An EVMNodeConfig instance with the fields given as parameters.
        """
        return EVMNodeConfig(node_id, parent_id, node_name, monitor_node,
                             node_http_url)

    def clear_attributes(self) -> None:
        """
        This function sets all attributes to None. It is mostly used for
        testing.
        """
        self._node_1 = None
        self._node_2 = None
