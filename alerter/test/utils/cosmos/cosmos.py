from src.configs.nodes.cosmos import CosmosNodeConfig


class CosmosTestNodes:
    def __init__(self) -> None:
        self._archive_validator = CosmosNodeConfig(
            'node_id_1', 'parent_id_1', 'node_name_1', True, True, 'prom_url_1',
            True, 'cosmos_rest_url_1', True, 'tendermint_rpc_url_1', True, True,
            True, 'operator_address_1')
        self._archive_non_validator = CosmosNodeConfig(
            'node_id_2', 'parent_id_2', 'node_name_2', True, True, 'prom_url_2',
            True, 'cosmos_rest_url_2', True, 'tendermint_rpc_url_2', False,
            True, True, 'operator_address_2')
        self._pruned_validator = CosmosNodeConfig(
            'node_id_3', 'parent_id_3', 'node_name_3', True, True, 'prom_url_3',
            True, 'cosmos_rest_url_3', True, 'tendermint_rpc_url_3', True,
            False, True, 'operator_address_3')
        self._pruned_non_validator = CosmosNodeConfig(
            'node_id_4', 'parent_id_4', 'node_name_4', True, True, 'prom_url_4',
            True, 'cosmos_rest_url_4', True, 'tendermint_rpc_url_4', False,
            False, True, 'operator_address_4')
        self._is_mev_tendermint_node = CosmosNodeConfig( 
            'node_id_4', 'parent_id_4', 'node_name_4', True, True, 'prom_url_4',
            True, 'cosmos_rest_url_4', True, 'tendermint_rpc_url_4', False,
            False, True, 'operator_address_4', is_mev_tendermint_node=True)

    @property
    def archive_validator(self) -> CosmosNodeConfig:
        return self._archive_validator

    @property
    def archive_non_validator(self) -> CosmosNodeConfig:
        return self._archive_non_validator

    @property
    def pruned_validator(self) -> CosmosNodeConfig:
        return self._pruned_validator

    @property
    def pruned_non_validator(self) -> CosmosNodeConfig:
        return self._pruned_non_validator

    @property
    def is_mev_tendermint_node(self) -> CosmosNodeConfig:
        return self._is_mev_tendermint_node

    @staticmethod
    def create_custom_node(
            node_id: str, parent_id: str, node_name: str, monitor_node: bool,
            monitor_prometheus: bool, prometheus_url: str,
            monitor_cosmos_rest: bool, cosmos_rest_url: str,
            monitor_tendermint_rpc: bool, tendermint_rpc_url: str,
            is_validator: bool, is_archive_node: bool, use_as_data_source: bool,
            operator_address: str) -> CosmosNodeConfig:
        """
        Given all the required fields to create an CosmosNodeConfig instance,
        this function will return a CosmosNodeConfig with the custom fields
        :param node_id: The node id
        :param parent_id: The parent id
        :param node_name: The node name
        :param monitor_node: Whether to monitor the node or not
        :param monitor_prometheus: Whether to monitor prometheus or not
        :param prometheus_url: The prometheus url
        :param monitor_cosmos_rest: Whether to monitor cosmos rest or not
        :param cosmos_rest_url: The cosmos rest url
        :param monitor_tendermint_rpc: Whether to monitor tendermint or not
        :param tendermint_rpc_url: The tendermint rpc url
        :param is_validator: Whether the node is a validator or not
        :param is_archive_node: Whether the node is an archive node or not
        :param use_as_data_source: Whether the node should be used as data
        source or not
        :param operator_address: The node's operator address
        :return:
        """
        return CosmosNodeConfig(
            node_id, parent_id, node_name, monitor_node, monitor_prometheus,
            prometheus_url, monitor_cosmos_rest, cosmos_rest_url,
            monitor_tendermint_rpc, tendermint_rpc_url, is_validator,
            is_archive_node, use_as_data_source, operator_address)

    def clear_attributes(self) -> None:
        """
        This function sets all attributes to None. It is mostly used for
        testing.
        """
        self._archive_non_validator = None
        self._archive_validator = None
        self._pruned_validator = None
        self._pruned_non_validator = None
