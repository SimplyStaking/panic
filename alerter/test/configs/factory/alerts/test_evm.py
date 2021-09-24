import copy
import unittest

from parameterized import parameterized

from src.configs.alerts.node.evm import EVMAlertsConfigsFactory
from src.configs.factory.node.evm_alerts import EVMNodeAlertsConfigsFactory
from src.utils.exceptions import ParentIdsMissMatchInAlertsConfiguration


class TestEVMAlertsConfigsFactory(unittest.TestCase):
    """
    Although currently there is only one type of EVM alerts config, the tests
    were conducted using parameterize.expand, just in case in the future we
    add more config types.
    """

    def setUp(self) -> None:
        # Some dummy values
        self.test_parent_id_1 = 'chain_name_d60b8a8e-9c70-4601-9103'
        self.test_parent_id_2 = 'chain_name_dbfsdg7s-sdff-4644-7456'
        self.test_chain_name_1 = 'chainlink matic'
        self.test_chain_name_2 = 'chainlink bsc'

        """
        First we will construct the received alerts configurations.
        """

        evm_config_metrics = [
            'evm_node_is_down', 'evm_block_syncing_block_height_difference',
            'evm_block_syncing_no_change_in_block_height',
        ]
        self.received_config_example_1_evm = {}
        self.received_config_example_2_evm = {}

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

        filtered_1_evm = {}
        for _, config in self.received_config_example_1_evm.items():
            filtered_1_evm[config['name']] = copy.deepcopy(config)

        filtered_2_evm = {}
        for _, config in self.received_config_example_2_evm.items():
            filtered_2_evm[config['name']] = copy.deepcopy(config)

        self.alerts_config_1_evm = EVMAlertsConfigsFactory(
            parent_id=self.test_parent_id_1,
            evm_node_is_down=filtered_1_evm['evm_node_is_down'],
            evm_block_syncing_block_height_difference=filtered_1_evm[
                'evm_block_syncing_block_height_difference'],
            evm_block_syncing_no_change_in_block_height=filtered_1_evm[
                'evm_block_syncing_no_change_in_block_height']
        )
        self.alerts_config_2_evm = EVMAlertsConfigsFactory(
            parent_id=self.test_parent_id_2,
            evm_node_is_down=filtered_2_evm['evm_node_is_down'],
            evm_block_syncing_block_height_difference=filtered_2_evm[
                'evm_block_syncing_block_height_difference'],
            evm_block_syncing_no_change_in_block_height=filtered_2_evm[
                'evm_block_syncing_no_change_in_block_height']
        )

        self.evm_configs_factory = EVMNodeAlertsConfigsFactory()

    def tearDown(self) -> None:
        self.received_config_example_1_evm = None
        self.received_config_example_2_evm = None
        self.alerts_config_1_evm = None
        self.alerts_config_2_evm = None
        self.evm_configs_factory = None

    @parameterized.expand([
        ('self.evm_configs_factory', 'self.received_config_example_1_evm',
         'self.alerts_config_1_evm', 'self.received_config_example_2_evm',
         'self.alerts_config_2_evm',)
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
        ('self.evm_configs_factory', 'self.received_config_example_1_evm',)
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
        ('self.evm_configs_factory', 'self.alerts_config_1_evm',
         'self.alerts_config_2_evm',)
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
        ('self.evm_configs_factory', 'self.alerts_config_1_evm',
         'self.alerts_config_2_evm',)
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
        ('self.evm_configs_factory', 'self.alerts_config_1_evm',
         'self.alerts_config_2_evm',)
    ])
    def test_config_exists_returns_true_if_config_exists(
            self, configs_factory, alerts_config_1, alerts_config_2) -> None:
        configs_factory = eval(configs_factory)
        alerts_config_1 = eval(alerts_config_1)
        alerts_config_2 = eval(alerts_config_2)

        state = {
            self.test_chain_name_1: alerts_config_1,
            self.test_chain_name_2: alerts_config_2
        }
        configs_factory._configs = state
        self.assertTrue(configs_factory.config_exists(self.test_chain_name_1))

    @parameterized.expand([
        ('self.evm_configs_factory', 'self.alerts_config_1_evm',)
    ])
    def test_config_exists_returns_false_if_config_does_not_exists(
            self, configs_factory, alerts_config_1) -> None:
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
        self.assertFalse(configs_factory.config_exists('bad_chain'))
        self.assertFalse(configs_factory.config_exists(self.test_chain_name_2))

    @parameterized.expand([
        ('self.evm_configs_factory', 'self.alerts_config_1_evm',
         'self.alerts_config_2_evm',)
    ])
    def test_get_parent_id_gets_id_from_stored_config_if_chain_exists_in_state(
            self, configs_factory, alerts_config_1, alerts_config_2) -> None:
        configs_factory = eval(configs_factory)
        alerts_config_1 = eval(alerts_config_1)
        alerts_config_2 = eval(alerts_config_2)

        state = {
            self.test_chain_name_1: alerts_config_1,
            self.test_chain_name_2: alerts_config_2
        }
        configs_factory._configs = state

        actual_output = configs_factory.get_parent_id(self.test_chain_name_1)
        self.assertEqual(self.test_parent_id_1, actual_output)

    @parameterized.expand([
        ('self.evm_configs_factory', 'self.alerts_config_1_evm',)
    ])
    def test_get_parent_id_returns_none_if_chain_does_not_exist_in_state(
            self, configs_factory, alerts_config_1) -> None:
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
        self.assertIsNone(configs_factory.get_parent_id(self.test_chain_name_2))
        self.assertIsNone(configs_factory.get_parent_id('bad_chain'))

    @parameterized.expand([
        ('self.evm_configs_factory', 'self.alerts_config_1_evm',
         'self.alerts_config_2_evm',)
    ])
    def test_get_chain_name_gets_name_given_the_parent_id_if_config_exists(
            self, configs_factory, alerts_config_1, alerts_config_2) -> None:
        configs_factory = eval(configs_factory)
        alerts_config_1 = eval(alerts_config_1)
        alerts_config_2 = eval(alerts_config_2)

        state = {
            self.test_chain_name_1: alerts_config_1,
            self.test_chain_name_2: alerts_config_2
        }
        configs_factory._configs = state

        actual_output = configs_factory.get_chain_name(self.test_parent_id_1)
        self.assertEqual(self.test_chain_name_1, actual_output)

    @parameterized.expand([
        ('self.evm_configs_factory', 'self.alerts_config_1_evm',)
    ])
    def test_get_chain_name_returns_none_if_no_config_exists_for_parent_id(
            self, configs_factory, alerts_config_1) -> None:
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
        self.assertIsNone(configs_factory.get_chain_name(self.test_parent_id_2))
        self.assertIsNone(configs_factory.get_chain_name('bad_id'))
