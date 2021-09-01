import copy
import unittest

from src.configs.alerts.node.chainlink import ChainlinkNodeAlertsConfig
from src.configs.alerts.node.evm import EVMNodeAlertsConfig
from src.configs.factory.chainlink_alerts_configs_factory import (
    ChainlinkAlertsConfigsFactory)
from src.configs.factory.evm_alerts_configs_factory import (
    EVMAlertsConfigsFactory)
from src.utils.exceptions import ParentIdsMissMatchInAlertsConfiguration


class TestAlertsConfigsFactory(unittest.TestCase):
    """
    This test suite tests all the different alerts configs factories. This was
    done in this way to avoid code duplication.
    """
    def setUp(self) -> None:
        # Some dummy values
        self.test_parent_id_1 = 'chain_name_d60b8a8e-9c70-4601-9103'
        self.test_parent_id_2 = 'chain_name_dbfsdg7s-sdff-4644-7456'
        self.test_chain_name_1 = 'chainlink matic'
        self.test_chain_name_2 = 'chainlink bsc'

        """
        First we will construct the received alerts configurations for both
        Chainlink and EVM chains
        """

        chainlink_config_metrics = [
            'system_is_down', 'open_file_descriptors', 'system_cpu_usage',
            'system_storage_usage', 'system_ram_usage',
            'head_tracker_current_head', 'head_tracker_heads_received_total',
            'tx_manager_gas_bump_exceeds_limit_total', 'eth_balance_amount',
            'unconfirmed_transactions', 'run_status_update_total',
            'max_unconfirmed_blocks', 'eth_balance_amount_increase',
            'process_start_time_seconds', 'node_is_down'
        ]
        evm_config_metrics = [
            'evm_node_is_down', 'evm_block_syncing_block_height_difference',
            'evm_block_syncing_no_change_in_block_height',
        ]

        self.received_config_example_1_chainlink = {}
        self.received_config_example_2_chainlink = {}
        self.received_config_example_1_evm = {}
        self.received_config_example_2_evm = {}

        for i in range(len(chainlink_config_metrics)):
            self.received_config_example_1_chainlink[str(i)] = {
                'name': chainlink_config_metrics[i],
                'parent_id': self.test_parent_id_1
            }
            self.received_config_example_2_chainlink[str(i)] = {
                'name': chainlink_config_metrics[i],
                'parent_id': self.test_parent_id_2
            }
        for i in range(len(evm_config_metrics)):
            self.received_config_example_1_evm[str(i)] = {
                'name': evm_config_metrics[i],
                'parent_id': self.test_parent_id_1
            }
            self.received_config_example_2_evm[str(i)] = {
                'name': evm_config_metrics[i],
                'parent_id': self.test_parent_id_2
            }

        """
        Now we will construct the expected config objects
        """

        filtered_1_chainlink = {}
        for _, config in self.received_config_example_1_chainlink.items():
            filtered_1_chainlink[config['name']] = copy.deepcopy(config)

        filtered_2_chainlink = {}
        for _, config in self.received_config_example_2_chainlink.items():
            filtered_2_chainlink[config['name']] = copy.deepcopy(config)

        filtered_1_evm = {}
        for _, config in self.received_config_example_1_evm.items():
            filtered_1_evm[config['name']] = copy.deepcopy(config)

        filtered_2_evm = {}
        for _, config in self.received_config_example_2_evm.items():
            filtered_2_evm[config['name']] = copy.deepcopy(config)

        self.alerts_config_1_chainlink = ChainlinkNodeAlertsConfig(
            parent_id=self.test_parent_id_1,
            head_tracker_current_head=filtered_1_chainlink[
                'head_tracker_current_head'],
            head_tracker_heads_received_total=filtered_1_chainlink[
                'head_tracker_heads_received_total'],
            max_unconfirmed_blocks=filtered_1_chainlink[
                'max_unconfirmed_blocks'],
            process_start_time_seconds=filtered_1_chainlink[
                'process_start_time_seconds'],
            tx_manager_gas_bump_exceeds_limit_total=filtered_1_chainlink[
                'tx_manager_gas_bump_exceeds_limit_total'],
            unconfirmed_transactions=filtered_1_chainlink[
                'unconfirmed_transactions'],
            run_status_update_total=filtered_1_chainlink[
                'run_status_update_total'],
            eth_balance_amount=filtered_1_chainlink['eth_balance_amount'],
            eth_balance_amount_increase=filtered_1_chainlink[
                'eth_balance_amount_increase'],
            node_is_down=filtered_1_chainlink['node_is_down']
        )
        self.alerts_config_2_chainlink = ChainlinkNodeAlertsConfig(
            parent_id=self.test_parent_id_2,
            head_tracker_current_head=filtered_2_chainlink[
                'head_tracker_current_head'],
            head_tracker_heads_received_total=filtered_2_chainlink[
                'head_tracker_heads_received_total'],
            max_unconfirmed_blocks=filtered_2_chainlink[
                'max_unconfirmed_blocks'],
            process_start_time_seconds=filtered_2_chainlink[
                'process_start_time_seconds'],
            tx_manager_gas_bump_exceeds_limit_total=filtered_2_chainlink[
                'tx_manager_gas_bump_exceeds_limit_total'],
            unconfirmed_transactions=filtered_2_chainlink[
                'unconfirmed_transactions'],
            run_status_update_total=filtered_2_chainlink[
                'run_status_update_total'],
            eth_balance_amount=filtered_2_chainlink['eth_balance_amount'],
            eth_balance_amount_increase=filtered_2_chainlink[
                'eth_balance_amount_increase'],
            node_is_down=filtered_2_chainlink['node_is_down']
        )
        self.alerts_config_1_evm = EVMNodeAlertsConfig(
            parent_id=self.test_parent_id_1,
            evm_node_is_down=filtered_1_evm['evm_node_is_down'],
            evm_block_syncing_block_height_difference=filtered_1_evm[
                'evm_block_syncing_block_height_difference'],
            evm_block_syncing_no_change_in_block_height=filtered_1_evm[
                'evm_block_syncing_no_change_in_block_height']
        )
        self.alerts_config_2_evm = EVMNodeAlertsConfig(
            parent_id=self.test_parent_id_2,
            evm_node_is_down=filtered_2_evm['evm_node_is_down'],
            evm_block_syncing_block_height_difference=filtered_2_evm[
                'evm_block_syncing_block_height_difference'],
            evm_block_syncing_no_change_in_block_height=filtered_2_evm[
                'evm_block_syncing_no_change_in_block_height']
        )

        self.chainlink_configs_factory = ChainlinkAlertsConfigsFactory()
        self.evm_configs_factory = EVMAlertsConfigsFactory()

    def tearDown(self) -> None:
        self.received_config_example_1_chainlink = None
        self.received_config_example_2_chainlink = None
        self.received_config_example_1_evm = None
        self.received_config_example_2_evm = None
        self.alerts_config_1_chainlink = None
        self.alerts_config_2_chainlink = None
        self.alerts_config_1_evm = None
        self.alerts_config_2_evm = None
        self.chainlink_configs_factory = None
        self.evm_configs_factory = None

    # def test_add_new_config_adds_a_new_config(self) -> None:
    #     """
    #     In this test we will check that add_new_config adds the newly received
    #     config correctly in the state. First we will test for when the state is
    #     empty and then for when the state is non-empty.
    #     """
    #     # First check that the state is empty
    #     self.assertEqual({}, self.chainlink_configs_factory.configs)
    #
    #     # Add a config and check that the state was modified correctly
    #     self.chainlink_configs_factory.add_new_config(self.test_chain_name_1,
    #                                                   self.received_config_example_1_chainlink)
    #     expected_state = {
    #         self.test_chain_name_1: self.alerts_config_1_chainlink
    #     }
    #     self.assertEqual(expected_state, self.chainlink_configs_factory.configs)
    #
    #     # Add another config and check that the state was modified correctly
    #     self.chainlink_configs_factory.add_new_config(self.test_chain_name_2,
    #                                                   self.received_config_example_2_chainlink)
    #     expected_state = {
    #         self.test_chain_name_1: self.alerts_config_1_chainlink,
    #         self.test_chain_name_2: self.alerts_config_2_chainlink
    #     }
    #     self.assertEqual(expected_state, self.chainlink_configs_factory.configs)
    #
    # def test_add_new_config_raises_ParentIdsMissMatch_if_parent_ids_not_equal(
    #         self) -> None:
    #     """
    #     In this test we will check that the specified exception is raised and
    #     that the state is not modified
    #     """
    #     self.received_config_example_1_chainlink['1']['parent_id'] = 'bad_parent_id'
    #     old_state = copy.deepcopy(self.chainlink_configs_factory.configs)
    #
    #     self.assertRaises(ParentIdsMissMatchInAlertsConfiguration,
    #                       self.chainlink_configs_factory.add_new_config,
    #                       self.test_chain_name_1,
    #                       self.received_config_example_1_chainlink)
    #     self.assertEqual(old_state, self.chainlink_configs_factory.configs)
    #
    # def test_remove_config_removes_config_for_chain_if_chain_exists(
    #         self) -> None:
    #     state = {
    #         self.test_chain_name_1: self.alerts_config_1_chainlink,
    #         self.test_chain_name_2: self.alerts_config_2_chainlink
    #     }
    #     self.chainlink_configs_factory._configs = state
    #
    #     self.chainlink_configs_factory.remove_config(self.test_chain_name_1)
    #     expected_state = {
    #         self.test_chain_name_2: self.alerts_config_2_chainlink
    #     }
    #     self.assertEqual(expected_state, self.chainlink_configs_factory.configs)
    #
    # def test_remove_config_does_nothing_if_no_config_exists_for_chain(
    #         self) -> None:
    #     """
    #     We will check that the state is kept intact if a configuration does not
    #     exist for a chain
    #     """
    #     state = {
    #         self.test_chain_name_1: self.alerts_config_1_chainlink,
    #         self.test_chain_name_2: self.alerts_config_2_chainlink
    #     }
    #     self.chainlink_configs_factory._configs = state
    #
    #     self.chainlink_configs_factory.remove_config('bad_chain')
    #     self.assertEqual(state, self.chainlink_configs_factory.configs)
    #
    # def test_config_exists_returns_true_if_config_exists(self) -> None:
    #     state = {
    #         self.test_chain_name_1: self.alerts_config_1_chainlink,
    #         self.test_chain_name_2: self.alerts_config_2_chainlink
    #     }
    #     self.chainlink_configs_factory._configs = state
    #     self.assertTrue(self.chainlink_configs_factory.config_exists(
    #         self.test_chain_name_1))
    #
    # def test_config_exists_returns_false_if_config_does_not_exists(
    #         self) -> None:
    #     """
    #     We will perform this test for both when the expected config object is
    #     invalid and for when the chain_name does not exist in the state
    #     """
    #     state = {
    #         self.test_chain_name_1: self.alerts_config_1_chainlink,
    #         self.test_chain_name_2: 'bad_object'
    #     }
    #     self.chainlink_configs_factory._configs = state
    #     self.assertFalse(self.chainlink_configs_factory.config_exists('bad_chain'))
    #     self.assertFalse(self.chainlink_configs_factory.config_exists(
    #         self.test_chain_name_2))
    #
    # def test_get_parent_id_gets_id_from_stored_config_if_chain_exists_in_state(
    #         self) -> None:
    #     state = {
    #         self.test_chain_name_1: self.alerts_config_1_chainlink,
    #         self.test_chain_name_2: self.alerts_config_2_chainlink
    #     }
    #     self.chainlink_configs_factory._configs = state
    #
    #     actual_output = self.chainlink_configs_factory.get_parent_id(
    #         self.test_chain_name_1)
    #     self.assertEqual(self.test_parent_id_1, actual_output)
    #
    # def test_get_parent_id_returns_none_if_chain_does_not_exist_in_state(
    #         self) -> None:
    #     """
    #     We will perform this test for both when the expected config object is
    #     invalid and for when the chain_name does not exist in the state
    #     """
    #     state = {
    #         self.test_chain_name_1: self.alerts_config_1_chainlink,
    #         self.test_chain_name_2: 'bad_object'
    #     }
    #     self.chainlink_configs_factory._configs = state
    #     self.assertIsNone(self.chainlink_configs_factory.get_parent_id(
    #         self.test_chain_name_2))
    #     self.assertIsNone(self.chainlink_configs_factory.get_parent_id('bad_chain'))
    #
    # def test_get_chain_name_gets_name_given_the_parent_id_if_config_exists(
    #         self) -> None:
    #     state = {
    #         self.test_chain_name_1: self.alerts_config_1_chainlink,
    #         self.test_chain_name_2: self.alerts_config_2_chainlink
    #     }
    #     self.chainlink_configs_factory._configs = state
    #
    #     actual_output = self.chainlink_configs_factory.get_chain_name(
    #         self.test_parent_id_1)
    #     self.assertEqual(self.test_chain_name_1, actual_output)
    #
    # def test_get_chain_name_returns_none_if_no_config_exists_for_parent_id(
    #         self) -> None:
    #     """
    #     We will perform this test for both when the expected config object is
    #     invalid and for when no config is associated with the given parent_id
    #     """
    #     state = {
    #         self.test_chain_name_1: self.alerts_config_1_chainlink,
    #         self.test_chain_name_2: 'bad_object'
    #     }
    #     self.chainlink_configs_factory._configs = state
    #     self.assertIsNone(self.chainlink_configs_factory.get_chain_name(
    #         self.test_parent_id_2))
    #     self.assertIsNone(self.chainlink_configs_factory.get_chain_name('bad_id'))