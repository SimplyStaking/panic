import copy
import unittest

from parameterized import parameterized

from src.configs.alerts.network.cosmos import CosmosNetworkAlertsConfig
from src.configs.alerts.node.cosmos import CosmosNodeAlertsConfig
from src.configs.factory.alerts.cosmos_alerts import (
    CosmosNodeAlertsConfigsFactory, CosmosNetworkAlertsConfigsFactory)
from src.utils.exceptions import ParentIdsMissMatchInAlertsConfiguration


class TestCosmosAlertsConfigsFactory(unittest.TestCase):
    def setUp(self) -> None:
        # Some dummy values
        self.test_parent_id_1 = 'chain_name_d60b8a8e-9c70-4601-9103'
        self.test_parent_id_2 = 'chain_name_dbfsdg7s-sdff-4644-7456'
        self.test_chain_name_1 = 'cosmos cosmos-hub'
        self.test_chain_name_2 = 'cosmos regen'

        """
        First we will construct the received alerts configurations.
        """

        cosmos_node_config_metrics = [
            'cannot_access_validator', 'cannot_access_node',
            'no_change_in_block_height_validator',
            'no_change_in_block_height_node', 'block_height_difference',
            'cannot_access_prometheus_validator',
            'cannot_access_prometheus_node',
            'cannot_access_cosmos_rest_validator',
            'cannot_access_cosmos_rest_node',
            'cannot_access_tendermint_rpc_validator',
            'cannot_access_tendermint_rpc_node', 'missed_blocks', 'slashed',
            'node_is_syncing', 'validator_is_syncing',
            'node_is_peered_with_sentinel', 'validator_is_peered_with_sentinel',
            'validator_not_active_in_session', 'validator_is_jailed'
        ]
        cosmos_network_config_metrics = ['new_proposal', 'proposal_concluded']
        self.received_config_example_1_cosmos_node = {}
        self.received_config_example_2_cosmos_node = {}
        self.received_config_example_3_cosmos_node = {}
        self.received_config_example_1_cosmos_network = {}
        self.received_config_example_2_cosmos_network = {}

        for i in range(len(cosmos_node_config_metrics)):
            self.received_config_example_1_cosmos_node[str(i)] = {
                'name': cosmos_node_config_metrics[i],
                'parent_id': self.test_parent_id_1
            }
            self.received_config_example_2_cosmos_node[str(i)] = {
                'name': cosmos_node_config_metrics[i],
                'parent_id': self.test_parent_id_2
            }

        for i in range(len(cosmos_network_config_metrics)):
            self.received_config_example_1_cosmos_network[str(i)] = {
                'name': cosmos_network_config_metrics[i],
                'parent_id': self.test_parent_id_1
            }
            self.received_config_example_2_cosmos_network[str(i)] = {
                'name': cosmos_network_config_metrics[i],
                'parent_id': self.test_parent_id_2
            }
        """
        Now we will construct the expected config objects
        """

        filtered_1_cosmos_node = {}
        for _, config in self.received_config_example_1_cosmos_node.items():
            filtered_1_cosmos_node[config['name']] = copy.deepcopy(config)

        filtered_2_cosmos_node = {}
        for _, config in self.received_config_example_2_cosmos_node.items():
            filtered_2_cosmos_node[config['name']] = copy.deepcopy(config)

        filtered_1_cosmos_network = {}
        for _, config in self.received_config_example_1_cosmos_network.items():
            filtered_1_cosmos_network[config['name']] = copy.deepcopy(config)

        filtered_2_cosmos_network = {}
        for _, config in self.received_config_example_2_cosmos_network.items():
            filtered_2_cosmos_network[config['name']] = copy.deepcopy(config)

        self.alerts_config_1_cosmos_node = CosmosNodeAlertsConfig(
            parent_id=self.test_parent_id_1,
            cannot_access_validator=filtered_1_cosmos_node[
                "cannot_access_validator"],
            cannot_access_node=filtered_1_cosmos_node["cannot_access_node"],
            validator_not_active_in_session=filtered_1_cosmos_node[
                "validator_not_active_in_session"],
            no_change_in_block_height_validator=filtered_1_cosmos_node[
                "no_change_in_block_height_validator"],
            no_change_in_block_height_node=filtered_1_cosmos_node[
                "no_change_in_block_height_node"],
            block_height_difference=filtered_1_cosmos_node[
                "block_height_difference"],
            cannot_access_prometheus_validator=filtered_1_cosmos_node[
                "cannot_access_prometheus_validator"],
            cannot_access_prometheus_node=filtered_1_cosmos_node[
                "cannot_access_prometheus_node"],
            cannot_access_cosmos_rest_validator=filtered_1_cosmos_node[
                "cannot_access_cosmos_rest_validator"],
            cannot_access_cosmos_rest_node=filtered_1_cosmos_node[
                "cannot_access_cosmos_rest_node"],
            cannot_access_tendermint_rpc_validator=filtered_1_cosmos_node[
                "cannot_access_tendermint_rpc_validator"],
            cannot_access_tendermint_rpc_node=filtered_1_cosmos_node[
                "cannot_access_tendermint_rpc_node"],
            missed_blocks=filtered_1_cosmos_node["missed_blocks"],
            slashed=filtered_1_cosmos_node["slashed"],
            node_is_syncing=filtered_1_cosmos_node["node_is_syncing"],
            validator_is_syncing=filtered_1_cosmos_node["validator_is_syncing"],
            validator_is_jailed=filtered_1_cosmos_node["validator_is_jailed"],
            node_is_peered_with_sentinel=filtered_1_cosmos_node['node_is_peered_with_sentinel'],
            validator_is_peered_with_sentinel=filtered_1_cosmos_node['validator_is_peered_with_sentinel'],
        )



        self.alerts_config_2_cosmos_node = CosmosNodeAlertsConfig(
            parent_id=self.test_parent_id_2,
            cannot_access_validator=filtered_2_cosmos_node[
                "cannot_access_validator"],
            cannot_access_node=filtered_2_cosmos_node["cannot_access_node"],
            validator_not_active_in_session=filtered_2_cosmos_node[
                "validator_not_active_in_session"],
            no_change_in_block_height_validator=filtered_2_cosmos_node[
                "no_change_in_block_height_validator"],
            no_change_in_block_height_node=filtered_2_cosmos_node[
                "no_change_in_block_height_node"],
            block_height_difference=filtered_2_cosmos_node[
                "block_height_difference"],
            cannot_access_prometheus_validator=filtered_2_cosmos_node[
                "cannot_access_prometheus_validator"],
            cannot_access_prometheus_node=filtered_2_cosmos_node[
                "cannot_access_prometheus_node"],
            cannot_access_cosmos_rest_validator=filtered_2_cosmos_node[
                "cannot_access_cosmos_rest_validator"],
            cannot_access_cosmos_rest_node=filtered_2_cosmos_node[
                "cannot_access_cosmos_rest_node"],
            cannot_access_tendermint_rpc_validator=filtered_2_cosmos_node[
                "cannot_access_tendermint_rpc_validator"],
            cannot_access_tendermint_rpc_node=filtered_2_cosmos_node[
                "cannot_access_tendermint_rpc_node"],
            missed_blocks=filtered_2_cosmos_node["missed_blocks"],
            slashed=filtered_2_cosmos_node["slashed"],
            node_is_syncing=filtered_2_cosmos_node["node_is_syncing"],
            validator_is_syncing=filtered_2_cosmos_node["validator_is_syncing"],
            validator_is_jailed=filtered_2_cosmos_node["validator_is_jailed"],
            node_is_peered_with_sentinel=filtered_2_cosmos_node['node_is_peered_with_sentinel'],
            validator_is_peered_with_sentinel=filtered_2_cosmos_node['validator_is_peered_with_sentinel'],
        )

        self.alerts_config_1_cosmos_network = CosmosNetworkAlertsConfig(
            parent_id=self.test_parent_id_1,
            new_proposal=filtered_1_cosmos_network['new_proposal'],
            proposal_concluded=filtered_1_cosmos_network['proposal_concluded'],
        )
        self.alerts_config_2_cosmos_network = CosmosNetworkAlertsConfig(
            parent_id=self.test_parent_id_2,
            new_proposal=filtered_2_cosmos_network['new_proposal'],
            proposal_concluded=filtered_2_cosmos_network['proposal_concluded'],
        )

        self.cosmos_node_configs_factory = CosmosNodeAlertsConfigsFactory()
        self.cosmos_network_configs_factory = (
            CosmosNetworkAlertsConfigsFactory())

    def tearDown(self) -> None:
        self.received_config_example_1_cosmos_node = None
        self.received_config_example_2_cosmos_node = None
        self.received_config_example_1_cosmos_network = None
        self.received_config_example_2_cosmos_network = None
        self.alerts_config_1_cosmos_node = None
        self.alerts_config_2_cosmos_node = None
        self.alerts_config_1_cosmos_network = None
        self.alerts_config_2_cosmos_network = None
        self.cosmos_node_configs_factory = None
        self.cosmos_network_configs_factory = None

    @parameterized.expand([
        ('self.cosmos_node_configs_factory',
         'self.received_config_example_1_cosmos_node',
         'self.alerts_config_1_cosmos_node',
         'self.received_config_example_2_cosmos_node',
         'self.alerts_config_2_cosmos_node',),
        ('self.cosmos_network_configs_factory',
         'self.received_config_example_1_cosmos_network',
         'self.alerts_config_1_cosmos_network',
         'self.received_config_example_2_cosmos_network',
         'self.alerts_config_2_cosmos_network',)
    ])
    def test_add_new_config_adds_a_new_config(
            self, configs_factory, received_config_1, alerts_config_1,
            received_config_2, alerts_config_2) -> None:
        """
        In this test we will check that add_new_config adds the newly received
        config correctly in the state. First we will test for when the state is
        empty and then for when the state is non-empty.
        """
        configs_factory = eval(configs_factory)
        received_config_1 = eval(received_config_1)
        alerts_config_1 = eval(alerts_config_1)
        received_config_2 = eval(received_config_2)
        alerts_config_2 = eval(alerts_config_2)

        # First check that the state is empty
        self.assertEqual({}, configs_factory.configs)

        # Add a config and check that the state was modified correctly
        configs_factory.add_new_config(self.test_chain_name_1,
                                       received_config_1)
        expected_state = {
            self.test_chain_name_1: alerts_config_1
        }

        self.assertEqual(expected_state, configs_factory.configs)

        # Add another config and check that the state was modified correctly
        configs_factory.add_new_config(self.test_chain_name_2,
                                       received_config_2)
        expected_state = {
            self.test_chain_name_1: alerts_config_1,
            self.test_chain_name_2: alerts_config_2
        }

        self.assertEqual(expected_state, configs_factory.configs)

    @parameterized.expand([
        ('self.cosmos_node_configs_factory',
         'self.received_config_example_1_cosmos_node',),
        ('self.cosmos_network_configs_factory',
         'self.received_config_example_1_cosmos_network',)
    ])
    def test_add_new_config_raises_ParentIdsMissMatch_if_parent_ids_not_equal(
            self, configs_factory, received_config) -> None:
        """
        In this test we will check that the specified exception is raised and
        that the state is not modified
        """
        configs_factory = eval(configs_factory)
        received_config = eval(received_config)

        received_config['1']['parent_id'] = 'bad_parent_id'
        old_state = copy.deepcopy(configs_factory.configs)

        self.assertRaises(
            ParentIdsMissMatchInAlertsConfiguration,
            configs_factory.add_new_config, self.test_chain_name_1,
            received_config)
        self.assertEqual(old_state, configs_factory.configs)

    @parameterized.expand([
        ('self.cosmos_node_configs_factory', 'self.alerts_config_1_cosmos_node',
         'self.alerts_config_2_cosmos_node',),
        ('self.cosmos_network_configs_factory',
         'self.alerts_config_1_cosmos_network',
         'self.alerts_config_2_cosmos_network',)
    ])
    def test_remove_config_removes_config_for_chain_if_chain_exists(
            self, configs_factory, alerts_config_1, alerts_config_2) -> None:
        configs_factory = eval(configs_factory)
        alerts_config_1 = eval(alerts_config_1)
        alerts_config_2 = eval(alerts_config_2)

        state = {
            self.test_chain_name_1: alerts_config_1,
            self.test_chain_name_2: alerts_config_2
        }
        configs_factory._configs = state

        configs_factory.remove_config(self.test_chain_name_1)
        expected_state = {
            self.test_chain_name_2: alerts_config_2
        }
        self.assertEqual(expected_state, configs_factory.configs)

    @parameterized.expand([
        ('self.cosmos_node_configs_factory', 'self.alerts_config_1_cosmos_node',
         'self.alerts_config_2_cosmos_node',),
        ('self.cosmos_network_configs_factory',
         'self.alerts_config_1_cosmos_network',
         'self.alerts_config_2_cosmos_network',)
    ])
    def test_remove_config_does_nothing_if_no_config_exists_for_chain(
            self, configs_factory, alerts_config_1, alerts_config_2) -> None:
        """
        We will check that the state is kept intact if a configuration does not
        exist for a chain
        """
        configs_factory = eval(configs_factory)
        alerts_config_1 = eval(alerts_config_1)
        alerts_config_2 = eval(alerts_config_2)

        state = {
            self.test_chain_name_1: alerts_config_1,
            self.test_chain_name_2: alerts_config_2
        }
        configs_factory._configs = state

        configs_factory.remove_config('bad_chain')
        self.assertEqual(state, configs_factory.configs)

    @parameterized.expand([
        ('self.cosmos_node_configs_factory', 'self.alerts_config_1_cosmos_node',
         'self.alerts_config_2_cosmos_node', CosmosNodeAlertsConfig),
        ('self.cosmos_network_configs_factory',
         'self.alerts_config_1_cosmos_network',
         'self.alerts_config_2_cosmos_network', CosmosNetworkAlertsConfig)
    ])
    def test_config_exists_returns_true_if_config_exists(
            self, configs_factory, alerts_config_1, alerts_config_2,
            config_type) -> None:
        configs_factory = eval(configs_factory)
        alerts_config_1 = eval(alerts_config_1)
        alerts_config_2 = eval(alerts_config_2)

        state = {
            self.test_chain_name_1: alerts_config_1,
            self.test_chain_name_2: alerts_config_2
        }
        configs_factory._configs = state
        self.assertTrue(configs_factory.config_exists(self.test_chain_name_1,
                                                      config_type))

    @parameterized.expand([
        ('self.cosmos_node_configs_factory',
         'self.alerts_config_1_cosmos_node', CosmosNodeAlertsConfig),
        ('self.cosmos_network_configs_factory',
         'self.alerts_config_1_cosmos_network', CosmosNetworkAlertsConfig)
    ])
    def test_config_exists_returns_false_if_config_does_not_exists(
            self, configs_factory, alerts_config_1, config_type) -> None:
        """
        We will perform this test for both when the expected config object is
        invalid and for when the chain_name does not exist in the state
        """
        configs_factory = eval(configs_factory)
        alerts_config_1 = eval(alerts_config_1)

        state = {
            self.test_chain_name_1: alerts_config_1,
            self.test_chain_name_2: 'bad_object'
        }
        configs_factory._configs = state
        self.assertFalse(configs_factory.config_exists('bad_chain',
                                                       config_type))
        self.assertFalse(configs_factory.config_exists(self.test_chain_name_2,
                                                       config_type))

    @parameterized.expand([
        ('self.cosmos_node_configs_factory', 'self.alerts_config_1_cosmos_node',
         'self.alerts_config_2_cosmos_node', CosmosNodeAlertsConfig),
        ('self.cosmos_network_configs_factory',
         'self.alerts_config_1_cosmos_network',
         'self.alerts_config_2_cosmos_network', CosmosNetworkAlertsConfig)
    ])
    def test_get_parent_id_gets_id_from_stored_config_if_chain_exists_in_state(
            self, configs_factory, alerts_config_1, alerts_config_2,
            config_type) -> None:
        configs_factory = eval(configs_factory)
        alerts_config_1 = eval(alerts_config_1)
        alerts_config_2 = eval(alerts_config_2)

        state = {
            self.test_chain_name_1: alerts_config_1,
            self.test_chain_name_2: alerts_config_2
        }
        configs_factory._configs = state

        actual_output = configs_factory.get_parent_id(self.test_chain_name_1,
                                                      config_type)
        self.assertEqual(self.test_parent_id_1, actual_output)

    @parameterized.expand([
        ('self.cosmos_node_configs_factory',
         'self.alerts_config_1_cosmos_node', CosmosNodeAlertsConfig),
        ('self.cosmos_network_configs_factory',
         'self.alerts_config_1_cosmos_network', CosmosNetworkAlertsConfig)
    ])
    def test_get_parent_id_returns_none_if_chain_does_not_exist_in_state(
            self, configs_factory, alerts_config_1, config_type) -> None:
        """
        We will perform this test for both when the expected config object is
        invalid and for when the chain_name does not exist in the state
        """
        configs_factory = eval(configs_factory)
        alerts_config_1 = eval(alerts_config_1)

        state = {
            self.test_chain_name_1: alerts_config_1,
            self.test_chain_name_2: 'bad_object'
        }
        configs_factory._configs = state
        self.assertIsNone(configs_factory.get_parent_id(self.test_chain_name_2,
                                                        config_type))
        self.assertIsNone(configs_factory.get_parent_id('bad_chain',
                                                        config_type))

    @parameterized.expand([
        ('self.cosmos_node_configs_factory', 'self.alerts_config_1_cosmos_node',
         'self.alerts_config_2_cosmos_node', CosmosNodeAlertsConfig),
        ('self.cosmos_network_configs_factory',
         'self.alerts_config_1_cosmos_network',
         'self.alerts_config_2_cosmos_network', CosmosNetworkAlertsConfig)
    ])
    def test_get_chain_name_gets_name_given_the_parent_id_if_config_exists(
            self, configs_factory, alerts_config_1, alerts_config_2,
            config_type) -> None:
        configs_factory = eval(configs_factory)
        alerts_config_1 = eval(alerts_config_1)
        alerts_config_2 = eval(alerts_config_2)

        state = {
            self.test_chain_name_1: alerts_config_1,
            self.test_chain_name_2: alerts_config_2
        }
        configs_factory._configs = state

        actual_output = configs_factory.get_chain_name(self.test_parent_id_1,
                                                       config_type)
        self.assertEqual(self.test_chain_name_1, actual_output)

    @parameterized.expand([
        ('self.cosmos_node_configs_factory',
         'self.alerts_config_1_cosmos_node', CosmosNodeAlertsConfig),
        ('self.cosmos_network_configs_factory',
         'self.alerts_config_1_cosmos_network', CosmosNetworkAlertsConfig)
    ])
    def test_get_chain_name_returns_none_if_no_config_exists_for_parent_id(
            self, configs_factory, alerts_config_1, config_type) -> None:
        """
        We will perform this test for both when the expected config object is
        invalid and for when no config is associated with the given parent_id
        """
        configs_factory = eval(configs_factory)
        alerts_config_1 = eval(alerts_config_1)

        state = {
            self.test_chain_name_1: alerts_config_1,
            self.test_chain_name_2: 'bad_object'
        }
        configs_factory._configs = state
        self.assertIsNone(configs_factory.get_chain_name(self.test_parent_id_2,
                                                         config_type))
        self.assertIsNone(configs_factory.get_chain_name('bad_id', config_type))
