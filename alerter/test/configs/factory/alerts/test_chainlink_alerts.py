import copy
import unittest

from parameterized import parameterized

from src.configs.alerts.contract.chainlink import (
    ChainlinkContractAlertsConfig)
from src.configs.alerts.node.chainlink import ChainlinkNodeAlertsConfig
from src.configs.factory.alerts.chainlink_alerts import (
    ChainlinkNodeAlertsConfigsFactory, ChainlinkContractAlertsConfigsFactory
)
from src.utils.exceptions import ParentIdsMissMatchInAlertsConfiguration


class TestChainlinkAlertsConfigsFactory(unittest.TestCase):
    """
    This test suite tests all the different Chainlink alerts config factories.
    It is done using parameterized.expand. This was done in this way to avoid
    code duplication.
    """

    def setUp(self) -> None:
        # Some dummy values
        self.test_parent_id_1 = 'chain_name_d60b8a8e-9c70-4601-9103'
        self.test_parent_id_2 = 'chain_name_dbfsdg7s-sdff-4644-7456'
        self.test_chain_name_1 = 'chainlink matic'
        self.test_chain_name_2 = 'chainlink bsc'

        """
        First we will construct the received alerts configurations for both
        Chainlink Nodes and Chainlink Contracts
        """

        chainlink_node_config_metrics = [
            'head_tracker_current_head', 'head_tracker_heads_received_total',
            'tx_manager_gas_bump_exceeds_limit_total', 'balance_amount',
            'unconfirmed_transactions', 'run_status_update_total',
            'max_unconfirmed_blocks', 'balance_amount_increase',
            'process_start_time_seconds', 'node_is_down'
        ]
        chainlink_contracts_config_metrics = [
            'price_feed_not_observed', 'price_feed_deviation',
            'consensus_failure',
        ]

        self.received_config_example_1_cl_node = {}
        self.received_config_example_2_cl_node = {}
        self.received_config_example_1_cl_contract = {}
        self.received_config_example_2_cl_contract = {}

        for i in range(len(chainlink_node_config_metrics)):
            self.received_config_example_1_cl_node[str(i)] = {
                'name': chainlink_node_config_metrics[i],
                'parent_id': self.test_parent_id_1
            }
            self.received_config_example_2_cl_node[str(i)] = {
                'name': chainlink_node_config_metrics[i],
                'parent_id': self.test_parent_id_2
            }
        for i in range(len(chainlink_contracts_config_metrics)):
            self.received_config_example_1_cl_contract[str(i)] = {
                'name': chainlink_contracts_config_metrics[i],
                'parent_id': self.test_parent_id_1
            }
            self.received_config_example_2_cl_contract[str(i)] = {
                'name': chainlink_contracts_config_metrics[i],
                'parent_id': self.test_parent_id_2
            }

        """
        Now we will construct the expected config objects
        """

        filtered_1_cl_node = {}
        for _, config in self.received_config_example_1_cl_node.items():
            filtered_1_cl_node[config['name']] = copy.deepcopy(config)

        filtered_2_cl_node = {}
        for _, config in self.received_config_example_2_cl_node.items():
            filtered_2_cl_node[config['name']] = copy.deepcopy(config)

        filtered_1_cl_contract = {}
        for _, config in self.received_config_example_1_cl_contract.items():
            filtered_1_cl_contract[config['name']] = copy.deepcopy(config)

        filtered_2_cl_contract = {}
        for _, config in self.received_config_example_2_cl_contract.items():
            filtered_2_cl_contract[config['name']] = copy.deepcopy(config)

        self.alerts_config_1_cl_node = ChainlinkNodeAlertsConfig(
            parent_id=self.test_parent_id_1,
            head_tracker_current_head=filtered_1_cl_node[
                'head_tracker_current_head'],
            head_tracker_heads_received_total=filtered_1_cl_node[
                'head_tracker_heads_received_total'],
            max_unconfirmed_blocks=filtered_1_cl_node[
                'max_unconfirmed_blocks'],
            process_start_time_seconds=filtered_1_cl_node[
                'process_start_time_seconds'],
            tx_manager_gas_bump_exceeds_limit_total=filtered_1_cl_node[
                'tx_manager_gas_bump_exceeds_limit_total'],
            unconfirmed_transactions=filtered_1_cl_node[
                'unconfirmed_transactions'],
            run_status_update_total=filtered_1_cl_node[
                'run_status_update_total'],
            balance_amount=filtered_1_cl_node['balance_amount'],
            balance_amount_increase=filtered_1_cl_node[
                'balance_amount_increase'],
            node_is_down=filtered_1_cl_node['node_is_down']
        )
        self.alerts_config_2_cl_node = ChainlinkNodeAlertsConfig(
            parent_id=self.test_parent_id_2,
            head_tracker_current_head=filtered_2_cl_node[
                'head_tracker_current_head'],
            head_tracker_heads_received_total=filtered_2_cl_node[
                'head_tracker_heads_received_total'],
            max_unconfirmed_blocks=filtered_2_cl_node[
                'max_unconfirmed_blocks'],
            process_start_time_seconds=filtered_2_cl_node[
                'process_start_time_seconds'],
            tx_manager_gas_bump_exceeds_limit_total=filtered_2_cl_node[
                'tx_manager_gas_bump_exceeds_limit_total'],
            unconfirmed_transactions=filtered_2_cl_node[
                'unconfirmed_transactions'],
            run_status_update_total=filtered_2_cl_node[
                'run_status_update_total'],
            balance_amount=filtered_2_cl_node['balance_amount'],
            balance_amount_increase=filtered_2_cl_node[
                'balance_amount_increase'],
            node_is_down=filtered_2_cl_node['node_is_down']
        )
        self.alerts_config_1_cl_contract = ChainlinkContractAlertsConfig(
            parent_id=self.test_parent_id_1,
            price_feed_not_observed=filtered_1_cl_contract[
                'price_feed_not_observed'],
            price_feed_deviation=filtered_1_cl_contract['price_feed_deviation'],
            consensus_failure=filtered_1_cl_contract['consensus_failure']
        )
        self.alerts_config_2_cl_contract = ChainlinkContractAlertsConfig(
            parent_id=self.test_parent_id_2,
            price_feed_not_observed=filtered_2_cl_contract[
                'price_feed_not_observed'],
            price_feed_deviation=filtered_2_cl_contract['price_feed_deviation'],
            consensus_failure=filtered_2_cl_contract['consensus_failure'],
        )

        self.cl_node_configs_factory = ChainlinkNodeAlertsConfigsFactory()
        self.cl_contracts_configs_factory = \
            ChainlinkContractAlertsConfigsFactory()

    def tearDown(self) -> None:
        self.received_config_example_1_cl_node = None
        self.received_config_example_2_cl_node = None
        self.received_config_example_1_cl_contract = None
        self.received_config_example_2_cl_contract = None
        self.alerts_config_1_cl_node = None
        self.alerts_config_2_cl_node = None
        self.alerts_config_1_cl_contract = None
        self.alerts_config_2_cl_contract = None
        self.cl_node_configs_factory = None
        self.cl_contracts_configs_factory = None

    @parameterized.expand([
        ('self.cl_node_configs_factory',
         'self.received_config_example_1_cl_node',
         'self.alerts_config_1_cl_node',
         'self.received_config_example_2_cl_node',
         'self.alerts_config_2_cl_node',),
        ('self.cl_contracts_configs_factory',
         'self.received_config_example_1_cl_contract',
         'self.alerts_config_1_cl_contract',
         'self.received_config_example_2_cl_contract',
         'self.alerts_config_2_cl_contract',),
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
        ('self.cl_node_configs_factory',
         'self.received_config_example_1_cl_node',),
        ('self.cl_contracts_configs_factory',
         'self.received_config_example_1_cl_contract',),
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
        ('self.cl_node_configs_factory', 'self.alerts_config_1_cl_node',
         'self.alerts_config_2_cl_node',),
        ('self.cl_contracts_configs_factory',
         'self.alerts_config_1_cl_contract',
         'self.alerts_config_2_cl_contract',),
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
        ('self.cl_node_configs_factory', 'self.alerts_config_1_cl_node',
         'self.alerts_config_2_cl_node',),
        ('self.cl_contracts_configs_factory',
         'self.alerts_config_1_cl_contract',
         'self.alerts_config_2_cl_contract',),
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
        ('self.cl_node_configs_factory', 'self.alerts_config_1_cl_node',
         'self.alerts_config_2_cl_node', ChainlinkNodeAlertsConfig),
        ('self.cl_contracts_configs_factory',
         'self.alerts_config_1_cl_contract',
         'self.alerts_config_2_cl_contract', ChainlinkContractAlertsConfig),
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
        ('self.cl_node_configs_factory', 'self.alerts_config_1_cl_node',
         ChainlinkNodeAlertsConfig),
        ('self.cl_contracts_configs_factory',
         'self.alerts_config_1_cl_contract', ChainlinkContractAlertsConfig),
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
        ('self.cl_node_configs_factory', 'self.alerts_config_1_cl_node',
         'self.alerts_config_2_cl_node', ChainlinkNodeAlertsConfig),
        ('self.cl_contracts_configs_factory',
         'self.alerts_config_1_cl_contract', 'self.alerts_config_2_cl_contract',
         ChainlinkContractAlertsConfig),
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
        ('self.cl_node_configs_factory', 'self.alerts_config_1_cl_node',
         ChainlinkNodeAlertsConfig),
        ('self.cl_contracts_configs_factory',
         'self.alerts_config_1_cl_contract', ChainlinkContractAlertsConfig),
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
        ('self.cl_node_configs_factory', 'self.alerts_config_1_cl_node',
         'self.alerts_config_2_cl_node', ChainlinkNodeAlertsConfig),
        ('self.cl_contracts_configs_factory',
         'self.alerts_config_1_cl_contract', 'self.alerts_config_2_cl_contract',
         ChainlinkContractAlertsConfig),
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
        ('self.cl_node_configs_factory', 'self.alerts_config_1_cl_node',
         ChainlinkNodeAlertsConfig),
        ('self.cl_contracts_configs_factory',
         'self.alerts_config_1_cl_contract', ChainlinkContractAlertsConfig),
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
        self.assertIsNone(
            configs_factory.get_chain_name('bad_id', config_type))
