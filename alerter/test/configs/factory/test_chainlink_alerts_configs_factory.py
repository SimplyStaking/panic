import copy
import unittest

from src.configs.alerts.chainlink_node import ChainlinkNodeAlertsConfig
from src.configs.factory.chainlink_alerts_configs_factory import \
    ChainlinkAlertsConfigsFactory
from src.utils.exceptions import ParentIdsMissMatchInAlertsConfiguration


class TestChainlinkAlertsConfigsFactory(unittest.TestCase):
    def setUp(self) -> None:
        # Some dummy values
        self.test_parent_id_1 = 'chain_name_d60b8a8e-9c70-4601-9103'
        self.test_parent_id_2 = 'chain_name_dbfsdg7s-sdff-4644-7456'
        self.test_chain_name_1 = 'chainlink matic'
        self.test_chain_name_2 = 'chainlink bsc'

        # Construct received configs
        config_metrics = [
            'system_is_down', 'open_file_descriptors', 'system_cpu_usage',
            'system_storage_usage', 'system_ram_usage',
            'head_tracker_current_head', 'head_tracker_heads_received_total',
            'tx_manager_gas_bump_exceeds_limit_total', 'eth_balance_amount',
            'unconfirmed_transactions', 'head_tracker_num_heads_dropped_total',
            'run_status_update_total', 'head_tracker_heads_in_queue',
            'max_unconfirmed_blocks', 'eth_balance_amount_increase',
            'process_start_time_seconds', 'node_is_down'
        ]
        self.received_config_example_1 = {}
        self.received_config_example_2 = {}
        for i in range(len(config_metrics)):
            self.received_config_example_1[str(i)] = {
                'name': config_metrics[i],
                'parent_id': self.test_parent_id_1
            }
            self.received_config_example_2[str(i)] = {
                'name': config_metrics[i],
                'parent_id': self.test_parent_id_2
            }

        # Construct expected configs objects
        filtered_1 = {}
        for _, config in self.received_config_example_1.items():
            filtered_1[config['name']] = copy.deepcopy(config)
        filtered_2 = {}
        for _, config in self.received_config_example_2.items():
            filtered_2[config['name']] = copy.deepcopy(config)

        self.alerts_config_1 = ChainlinkNodeAlertsConfig(
            parent_id=self.test_parent_id_1,
            head_tracker_current_head=filtered_1['head_tracker_current_head'],
            head_tracker_heads_in_queue=filtered_1[
                'head_tracker_heads_in_queue'],
            head_tracker_heads_received_total=filtered_1[
                'head_tracker_heads_received_total'],
            head_tracker_num_heads_dropped_total=filtered_1[
                'head_tracker_num_heads_dropped_total'],
            max_unconfirmed_blocks=filtered_1['max_unconfirmed_blocks'],
            process_start_time_seconds=filtered_1['process_start_time_seconds'],
            tx_manager_gas_bump_exceeds_limit_total=filtered_1[
                'tx_manager_gas_bump_exceeds_limit_total'],
            unconfirmed_transactions=filtered_1['unconfirmed_transactions'],
            run_status_update_total=filtered_1['run_status_update_total'],
            eth_balance_amount=filtered_1['eth_balance_amount'],
            eth_balance_amount_increase=filtered_1[
                'eth_balance_amount_increase'],
            node_is_down=filtered_1['node_is_down']
        )
        self.alerts_config_2 = ChainlinkNodeAlertsConfig(
            parent_id=self.test_parent_id_2,
            head_tracker_current_head=filtered_2['head_tracker_current_head'],
            head_tracker_heads_in_queue=filtered_2[
                'head_tracker_heads_in_queue'],
            head_tracker_heads_received_total=filtered_2[
                'head_tracker_heads_received_total'],
            head_tracker_num_heads_dropped_total=filtered_2[
                'head_tracker_num_heads_dropped_total'],
            max_unconfirmed_blocks=filtered_2['max_unconfirmed_blocks'],
            process_start_time_seconds=filtered_2['process_start_time_seconds'],
            tx_manager_gas_bump_exceeds_limit_total=filtered_2[
                'tx_manager_gas_bump_exceeds_limit_total'],
            unconfirmed_transactions=filtered_2['unconfirmed_transactions'],
            run_status_update_total=filtered_2['run_status_update_total'],
            eth_balance_amount=filtered_2['eth_balance_amount'],
            eth_balance_amount_increase=filtered_2[
                'eth_balance_amount_increase'],
            node_is_down=filtered_2['node_is_down']
        )

        self.test_configs_factory = ChainlinkAlertsConfigsFactory()

    def tearDown(self) -> None:
        self.received_config_example_1 = None
        self.received_config_example_2 = None
        self.alerts_config_1 = None
        self.alerts_config_2 = None
        self.test_configs_factory = None

    def test_add_new_config_adds_a_new_config(self) -> None:
        """
        In this test we will check that add_new_config adds the newly received
        config correctly in the state. First we will test for when the state is
        empty and then for when the state is non-empty.
        """
        # First check that the state is empty
        self.assertEqual({}, self.test_configs_factory.configs)

        # Add a config and check that the state was modified correctly
        self.test_configs_factory.add_new_config(self.test_chain_name_1,
                                                 self.received_config_example_1)
        expected_state = {
            self.test_chain_name_1: self.alerts_config_1
        }
        self.assertEqual(expected_state, self.test_configs_factory.configs)

        # Add another config and check that the state was modified correctly
        self.test_configs_factory.add_new_config(self.test_chain_name_2,
                                                 self.received_config_example_2)
        expected_state = {
            self.test_chain_name_1: self.alerts_config_1,
            self.test_chain_name_2: self.alerts_config_2
        }
        self.assertEqual(expected_state, self.test_configs_factory.configs)

    def test_add_new_config_raises_ParentIdsMissMatch_if_parent_ids_not_equal(
            self) -> None:
        """
        In this test we will check that the specified exception is raised and
        that the state is not modified
        """
        self.received_config_example_1['1']['parent_id'] = 'bad_parent_id'
        old_state = copy.deepcopy(self.test_configs_factory.configs)

        self.assertRaises(ParentIdsMissMatchInAlertsConfiguration,
                          self.test_configs_factory.add_new_config,
                          self.test_chain_name_1,
                          self.received_config_example_1)
        self.assertEqual(old_state, self.test_configs_factory.configs)

    def test_remove_config_removes_config_for_chain_if_chain_exists(
            self) -> None:
        state = {
            self.test_chain_name_1: self.alerts_config_1,
            self.test_chain_name_2: self.alerts_config_2
        }
        self.test_configs_factory._configs = state

        self.test_configs_factory.remove_config(self.test_chain_name_1)
        expected_state = {
            self.test_chain_name_2: self.alerts_config_2
        }
        self.assertEqual(expected_state, self.test_configs_factory.configs)

    def test_remove_config_does_nothing_if_no_config_exists_for_chain(
            self) -> None:
        """
        We will check that the state is kept intact if a configuration does not
        exist for a chain
        """
        state = {
            self.test_chain_name_1: self.alerts_config_1,
            self.test_chain_name_2: self.alerts_config_2
        }
        self.test_configs_factory._configs = state

        self.test_configs_factory.remove_config('bad_chain')
        self.assertEqual(state, self.test_configs_factory.configs)

    def test_config_exists_returns_true_if_config_exists(self) -> None:
        state = {
            self.test_chain_name_1: self.alerts_config_1,
            self.test_chain_name_2: self.alerts_config_2
        }
        self.test_configs_factory._configs = state
        self.assertTrue(self.test_configs_factory.config_exists(
            self.test_chain_name_1))

    def test_config_exists_returns_false_if_config_does_not_exists(
            self) -> None:
        """
        We will perform this test for both when the expected config object is
        invalid and for when the chain_name does not exist in the state
        """
        state = {
            self.test_chain_name_1: self.alerts_config_1,
            self.test_chain_name_2: 'bad_object'
        }
        self.test_configs_factory._configs = state
        self.assertFalse(self.test_configs_factory.config_exists('bad_chain'))
        self.assertFalse(self.test_configs_factory.config_exists(
            self.test_chain_name_2))

    def test_get_parent_id_gets_id_from_stored_config_if_chain_exists_in_state(
            self) -> None:
        state = {
            self.test_chain_name_1: self.alerts_config_1,
            self.test_chain_name_2: self.alerts_config_2
        }
        self.test_configs_factory._configs = state

        actual_output = self.test_configs_factory.get_parent_id(
            self.test_chain_name_1)
        self.assertEqual(self.test_parent_id_1, actual_output)

    def test_get_parent_id_returns_none_if_chain_does_not_exist_in_state(
            self) -> None:
        """
        We will perform this test for both when the expected config object is
        invalid and for when the chain_name does not exist in the state
        """
        state = {
            self.test_chain_name_1: self.alerts_config_1,
            self.test_chain_name_2: 'bad_object'
        }
        self.test_configs_factory._configs = state
        self.assertIsNone(self.test_configs_factory.get_parent_id(
            self.test_chain_name_2))
        self.assertIsNone(self.test_configs_factory.get_parent_id('bad_chain'))

    def test_get_chain_name_gets_name_given_the_parent_id_if_config_exists(
            self) -> None:
        state = {
            self.test_chain_name_1: self.alerts_config_1,
            self.test_chain_name_2: self.alerts_config_2
        }
        self.test_configs_factory._configs = state

        actual_output = self.test_configs_factory.get_chain_name(
            self.test_parent_id_1)
        self.assertEqual(self.test_chain_name_1, actual_output)

    def test_get_chain_name_returns_none_if_no_config_exists_for_parent_id(
            self) -> None:
        """
        We will perform this test for both when the expected config object is
        invalid and for when no config is associated with the given parent_id
        """
        state = {
            self.test_chain_name_1: self.alerts_config_1,
            self.test_chain_name_2: 'bad_object'
        }
        self.test_configs_factory._configs = state
        self.assertIsNone(self.test_configs_factory.get_chain_name(
            self.test_parent_id_2))
        self.assertIsNone(self.test_configs_factory.get_chain_name('bad_id'))
