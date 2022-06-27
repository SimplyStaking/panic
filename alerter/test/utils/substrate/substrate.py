from src.configs.nodes.substrate import SubstrateNodeConfig


class SubstrateTestNodes:
    def __init__(self) -> None:
        self._archive_validator = SubstrateNodeConfig(
            'node_id_1', 'parent_id_1', 'node_name_1', True, 'node_ws_url_1',
            True, True, True, 'stash_address_1')
        self._archive_non_validator = SubstrateNodeConfig(
            'node_id_2', 'parent_id_2', 'node_name_2', True, 'node_ws_url_2',
            True, False, True, 'stash_address_2')
        self._pruned_validator = SubstrateNodeConfig(
            'node_id_3', 'parent_id_3', 'node_name_3', True, 'node_ws_url_3',
            True, True, False, 'stash_address_3')
        self._pruned_non_validator = SubstrateNodeConfig(
            'node_id_4', 'parent_id_4', 'node_name_4', True, 'node_ws_url_4',
            True, False, False, 'stash_address_4')

    @property
    def archive_validator(self) -> SubstrateNodeConfig:
        return self._archive_validator

    @property
    def archive_non_validator(self) -> SubstrateNodeConfig:
        return self._archive_non_validator

    @property
    def pruned_validator(self) -> SubstrateNodeConfig:
        return self._pruned_validator

    @property
    def pruned_non_validator(self) -> SubstrateNodeConfig:
        return self._pruned_non_validator

    @staticmethod
    def create_custom_node(
            node_id: str, parent_id: str, node_name: str, monitor_node: bool,
            node_ws_url: str, use_as_data_source: bool, is_validator: bool,
            is_archive_node: bool, stash_address: str) -> SubstrateNodeConfig:
        """
        Given all the required fields to create an SubstrateNodeConfig instance,
        this function will return a SubstrateNodeConfig with the custom fields
        :param node_id: The node id
        :param parent_id: The parent id
        :param node_name: The node name
        :param monitor_node: Whether to monitor the node or not
        :param node_ws_url: The websocket url of the node
        :param is_validator: Whether the node is a validator or not
        :param is_archive_node: Whether the node is an archive node or not
        :param use_as_data_source: Whether the node should be used as data
                                   source or not
        :param stash_address: The node's stash address
        :return: A new SubstrateNodeConfig instance based on the given
                 attributes
        """
        return SubstrateNodeConfig(
            node_id, parent_id, node_name, monitor_node, node_ws_url,
            use_as_data_source, is_validator, is_archive_node, stash_address)

    def clear_attributes(self) -> None:
        """
        This function sets all attributes to None. It is mostly used for
        testing.
        """
        self._archive_non_validator = None
        self._archive_validator = None
        self._pruned_validator = None
        self._pruned_non_validator = None
