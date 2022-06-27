import copy
import logging
import unittest
from datetime import datetime

from freezegun import freeze_time
from parameterized import parameterized

import src.alerter.alerts.network.cosmos as cosmos_alerts
from src.alerter.factory.cosmos_network_alerting_factory import (
    CosmosNetworkAlertingFactory)
from src.alerter.grouped_alerts_metric_code.network. \
    cosmos_network_metric_code import \
    GroupedCosmosNetworkAlertsMetricCode as AlertsMetricCode
from src.utils.exceptions import (NoSyncedDataSourceWasAccessibleException,
                                  CosmosNetworkDataCouldNotBeObtained)


class TestCosmosNetworkAlertingFactory(unittest.TestCase):
    def setUp(self) -> None:
        # Some dummy data and objects
        self.dummy_logger = logging.getLogger('dummy')
        self.test_parent_id_1 = 'test_parent_id_1'
        self.test_parent_id_2 = 'test_parent_id_2'
        self.test_chain_name = 'regen'
        self.test_dummy_state = 'dummy_state'

        # Test object
        self.cosmos_network_alerting_factory = CosmosNetworkAlertingFactory(
            self.dummy_logger)

    def tearDown(self) -> None:
        self.dummy_logger = None
        self.cosmos_network_alerting_factory = None

    def test_create_alerting_state_creates_the_correct_state(self) -> None:
        """
        In this test we will check that all alerting tools are created correctly
        for the given parent_id.
        """

        # We will also set a dummy state to confirm that the correct chain and
        # node are updated
        self.cosmos_network_alerting_factory._alerting_state = {
            self.test_parent_id_2: self.test_dummy_state
        }

        error_sent = {
            AlertsMetricCode.NoSyncedCosmosRestSource.value: False,
            AlertsMetricCode.CosmosNetworkDataNotObtained.value: False,
        }
        expected_state = {
            self.test_parent_id_1: {
                'error_sent': error_sent,
                'active_proposals': {},
            },
            self.test_parent_id_2: self.test_dummy_state
        }

        self.cosmos_network_alerting_factory.create_alerting_state(
            self.test_parent_id_1)
        self.assertDictEqual(
            expected_state, self.cosmos_network_alerting_factory.alerting_state)

    def test_create_alerting_state_same_state_if_created_and_unchanged_state(
            self) -> None:
        """
        In this test we will check that if a network's state is already created,
        the alerting state cannot be overwritten.
        """
        self.cosmos_network_alerting_factory._alerting_state = {
            self.test_parent_id_1: self.test_dummy_state,
            self.test_parent_id_2: self.test_dummy_state
        }
        expected_state = copy.deepcopy(
            self.cosmos_network_alerting_factory.alerting_state)

        self.cosmos_network_alerting_factory.create_alerting_state(
            self.test_parent_id_1)
        self.assertEqual(expected_state,
                         self.cosmos_network_alerting_factory.alerting_state)

    def test_remove_chain_alerting_state_removes_chain_alerting_state_correctly(
            self) -> None:
        """
        In this test we will check that the remove function removes the alerting
        state of the given chain
        """
        self.cosmos_network_alerting_factory._alerting_state = {
            self.test_parent_id_1: self.test_dummy_state,
            self.test_parent_id_2: self.test_dummy_state
        }
        expected_state = copy.deepcopy(
            self.cosmos_network_alerting_factory.alerting_state)
        del expected_state[self.test_parent_id_1]

        self.cosmos_network_alerting_factory.remove_chain_alerting_state(
            self.test_parent_id_1)
        self.assertEqual(expected_state,
                         self.cosmos_network_alerting_factory.alerting_state)

    def test_remove_chain_alerting_state_does_nothing_if_chain_does_not_exist(
            self) -> None:
        """
        In this test we will check that if no alerting state has been created
        for the chain, then the state is unmodified.
        """
        self.cosmos_network_alerting_factory._alerting_state = {
            self.test_parent_id_1: self.test_dummy_state,
            self.test_parent_id_2: self.test_dummy_state,
        }
        expected_state = copy.deepcopy(
            self.cosmos_network_alerting_factory.alerting_state)

        self.cosmos_network_alerting_factory.remove_chain_alerting_state(
            'bad_chain_id')
        self.assertEqual(expected_state,
                         self.cosmos_network_alerting_factory.alerting_state)

    @parameterized.expand([
        ('34', False,),
        (34, True,),
        (34.0, False,),
        (None, False,),
        ({}, False,),
        ({"key": 45}, False,),
        ([], False),
        (['val'], False),
    ])
    def test_proposal_id_valid_return(self, proposal_id,
                                      expected_return) -> None:
        """
        In this test we will check that self._proposal_id_valid returns as
        expected for multiple values
        """
        self.assertEqual(
            expected_return,
            self.cosmos_network_alerting_factory._proposal_id_valid(proposal_id)
        )

    def test_add_active_proposal_does_not_add_proposal_if_proposal_id_invalid(
            self) -> None:
        dummy_proposal = {'proposal_id': '45', 'title': 'light_test_prop'}
        self.cosmos_network_alerting_factory._alerting_state = {
            self.test_parent_id_1: {
                'error_sent': self.test_dummy_state,
                'active_proposals': {}
            },
            self.test_parent_id_2: {
                'error_sent': self.test_dummy_state,
                'active_proposals': {}
            },
        }
        expected_state = copy.deepcopy(
            self.cosmos_network_alerting_factory.alerting_state)

        self.cosmos_network_alerting_factory.add_active_proposal(
            self.test_parent_id_1, dummy_proposal, dummy_proposal['proposal_id']
        )
        self.assertEqual(expected_state,
                         self.cosmos_network_alerting_factory.alerting_state)

    def test_add_active_proposal_does_not_add_proposal_if_state_not_added(
            self) -> None:
        dummy_proposal = {'proposal_id': 45, 'title': 'light_test_prop'}
        self.cosmos_network_alerting_factory._alerting_state = {
            self.test_parent_id_2: {
                'error_sent': self.test_dummy_state,
                'active_proposals': {}
            },
        }
        expected_state = copy.deepcopy(
            self.cosmos_network_alerting_factory.alerting_state)

        self.cosmos_network_alerting_factory.add_active_proposal(
            self.test_parent_id_1, dummy_proposal, dummy_proposal['proposal_id']
        )
        self.assertEqual(expected_state,
                         self.cosmos_network_alerting_factory.alerting_state)

    def test_add_active_proposal_adds_proposal_correctly(self) -> None:
        """
        In this test we will check that the active_proposals dictionary is
        populated correctly. Here we will assume that the state was already
        created and the proposal_id is valid.
        """
        dummy_proposal_1 = {'proposal_id': 45, 'title': 'light_test_prop_1'}
        dummy_proposal_2 = {'proposal_id': 46, 'title': 'light_test_prop_2'}
        self.cosmos_network_alerting_factory._alerting_state = {
            self.test_parent_id_1: {
                'error_sent': self.test_dummy_state,
                'active_proposals': {
                    46: dummy_proposal_2
                }
            },
            self.test_parent_id_2: {
                'error_sent': self.test_dummy_state,
                'active_proposals': {}
            },
        }
        expected_state = copy.deepcopy(
            self.cosmos_network_alerting_factory.alerting_state)
        expected_state[self.test_parent_id_1]['active_proposals'][
            45] = dummy_proposal_1

        self.cosmos_network_alerting_factory.add_active_proposal(
            self.test_parent_id_1, dummy_proposal_1,
            dummy_proposal_1['proposal_id']
        )
        self.assertEqual(expected_state,
                         self.cosmos_network_alerting_factory.alerting_state)

    # TODO: The tests below should use logic which is similar to the add above

    def test_remove_active_proposal_does_not_remove_proposal_if_prop_id_invalid(
            self) -> None:
        dummy_proposal_1 = {'proposal_id': 45, 'title': 'light_test_prop'}
        dummy_proposal_2 = {'proposal_id': 46, 'title': 'light_test_prop'}
        self.cosmos_network_alerting_factory._alerting_state = {
            self.test_parent_id_1: {
                'error_sent': self.test_dummy_state,
                'active_proposals': {
                    45: dummy_proposal_1
                }
            },
            self.test_parent_id_2: {
                'error_sent': self.test_dummy_state,
                'active_proposals': {
                    46: dummy_proposal_2
                }
            },
        }
        expected_state = copy.deepcopy(
            self.cosmos_network_alerting_factory.alerting_state)

        self.cosmos_network_alerting_factory.remove_active_proposal(
            self.test_parent_id_1, '45',
        )
        self.assertEqual(expected_state,
                         self.cosmos_network_alerting_factory.alerting_state)

    def test_remove_active_proposal_does_nothing_if_state_not_added(
            self) -> None:
        """
        In this test we will check that the alerting state is kept intact if no
        alerting state has been created for a chain whose proposal should be
        removed
        """
        dummy_proposal_1 = {'proposal_id': 45, 'title': 'light_test_prop'}
        dummy_proposal_2 = {'proposal_id': 46, 'title': 'light_test_prop'}
        self.cosmos_network_alerting_factory._alerting_state = {
            self.test_parent_id_1: {
                'error_sent': self.test_dummy_state,
                'active_proposals': {
                    45: dummy_proposal_1
                }
            },
            self.test_parent_id_2: {
                'error_sent': self.test_dummy_state,
                'active_proposals': {
                    46: dummy_proposal_2
                }
            },
        }
        expected_state = copy.deepcopy(
            self.cosmos_network_alerting_factory.alerting_state)

        self.cosmos_network_alerting_factory.remove_active_proposal(
            self.test_parent_id_1, 47,
        )
        self.assertEqual(expected_state,
                         self.cosmos_network_alerting_factory.alerting_state)

    def test_remove_active_proposal_does_nothing_if_proposal_not_added(
            self) -> None:
        """
        In this test we will check that the alerting state is kept intact if the
        proposal to be removed has not been added yet
        """
        dummy_proposal_1 = {'proposal_id': 45, 'title': 'light_test_prop'}
        self.cosmos_network_alerting_factory._alerting_state = {
            self.test_parent_id_1: {
                'error_sent': self.test_dummy_state,
                'active_proposals': {
                    45: dummy_proposal_1
                }
            },
        }
        expected_state = copy.deepcopy(
            self.cosmos_network_alerting_factory.alerting_state)

        self.cosmos_network_alerting_factory.remove_active_proposal(
            self.test_parent_id_2, 45,
        )
        self.assertEqual(expected_state,
                         self.cosmos_network_alerting_factory.alerting_state)

    def test_remove_active_proposal_removes_correct_proposal_if_proposal_added(
            self) -> None:
        """
        In this test we will check that if the proposal to be removed has been
        added to the active list, then it is removed successfully.
        """
        dummy_proposal_1 = {'proposal_id': 45, 'title': 'light_test_prop'}
        dummy_proposal_2 = {'proposal_id': 46, 'title': 'light_test_prop'}
        self.cosmos_network_alerting_factory._alerting_state = {
            self.test_parent_id_1: {
                'error_sent': self.test_dummy_state,
                'active_proposals': {
                    45: dummy_proposal_1,
                    47: dummy_proposal_2,
                }
            },
            self.test_parent_id_2: {
                'error_sent': self.test_dummy_state,
                'active_proposals': {
                    46: dummy_proposal_2
                }
            },
        }
        expected_state = copy.deepcopy(
            self.cosmos_network_alerting_factory.alerting_state)
        del expected_state[self.test_parent_id_1]['active_proposals'][45]

        self.cosmos_network_alerting_factory.remove_active_proposal(
            self.test_parent_id_1, 45,
        )
        self.assertEqual(expected_state,
                         self.cosmos_network_alerting_factory.alerting_state)

    @parameterized.expand([
        ('bad_parent_id', 45, False,),
        ('bad_parent_id', '45', False,),
        ('test_parent_id_1', '45', False,),
        ('test_parent_id_2', '47', False,),
        ('test_parent_id_1', 45, True,),
        ('test_parent_id_2', 47, True,),
        ('test_parent_id_1', 51, False,),
        ('test_parent_id_2', 52, False,),
    ])
    def test_proposal_active_returns_as_expected(self, parent_id, proposal_id,
                                                 expected_return) -> None:
        dummy_proposal_1 = {'proposal_id': 45, 'title': 'light_test_prop'}
        dummy_proposal_2 = {'proposal_id': 46, 'title': 'light_test_prop'}
        dummy_proposal_3 = {'proposal_id': 47, 'title': 'light_test_prop'}
        dummy_proposal_4 = {'proposal_id': 48, 'title': 'light_test_prop'}
        self.cosmos_network_alerting_factory._alerting_state = {
            self.test_parent_id_1: {
                'error_sent': self.test_dummy_state,
                'active_proposals': {
                    45: dummy_proposal_1,
                    46: dummy_proposal_2,
                }
            },
            self.test_parent_id_2: {
                'error_sent': self.test_dummy_state,
                'active_proposals': {
                    47: dummy_proposal_3,
                    48: dummy_proposal_4,
                }
            },
        }

        actual_return = self.cosmos_network_alerting_factory.proposal_active(
            parent_id, proposal_id)
        self.assertEqual(expected_return, actual_return)

    @freeze_time("2012-01-01")
    def test_classify_error_alert_raises_error_alert_if_matched_error_codes(
            self) -> None:
        test_err = NoSyncedDataSourceWasAccessibleException('test_component',
                                                            'test_source')
        data_for_alerting = []
        self.cosmos_network_alerting_factory.create_alerting_state(
            self.test_parent_id_1)

        self.cosmos_network_alerting_factory.classify_error_alert(
            test_err.code,
            cosmos_alerts.ErrorNoSyncedCosmosRestDataSourcesAlert,
            cosmos_alerts.SyncedCosmosRestDataSourcesFoundAlert,
            data_for_alerting, self.test_parent_id_1, self.test_parent_id_1,
            self.test_chain_name, datetime.now().timestamp(),
            AlertsMetricCode.NoSyncedCosmosRestSource.value, "error msg",
            "resolved msg", test_err.code
        )

        expected_alert = cosmos_alerts.ErrorNoSyncedCosmosRestDataSourcesAlert(
            self.test_chain_name, 'error msg', 'ERROR',
            datetime.now().timestamp(), self.test_parent_id_1,
            self.test_parent_id_1)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_error_alert_does_nothing_if_no_err_received_and_no_raised(
            self) -> None:
        test_err = NoSyncedDataSourceWasAccessibleException('test_component',
                                                            'test_source')
        data_for_alerting = []
        self.cosmos_network_alerting_factory.create_alerting_state(
            self.test_parent_id_1)

        self.cosmos_network_alerting_factory.classify_error_alert(
            test_err.code,
            cosmos_alerts.ErrorNoSyncedCosmosRestDataSourcesAlert,
            cosmos_alerts.SyncedCosmosRestDataSourcesFoundAlert,
            data_for_alerting, self.test_parent_id_1, self.test_parent_id_1,
            self.test_chain_name, datetime.now().timestamp(),
            AlertsMetricCode.NoSyncedCosmosRestSource.value, "error msg",
            "resolved msg", None
        )

        self.assertEqual([], data_for_alerting)

    @parameterized.expand([
        (None,), (CosmosNetworkDataCouldNotBeObtained().code,),
    ])
    @freeze_time("2012-01-01")
    def test_classify_error_alert_raises_err_solved_if_alerted_and_no_error(
            self, code) -> None:
        """
        In this test we will check that an error solved alert is raised whenever
        no error is detected or a new error is detected after reporting a
        different error
        """
        test_err = NoSyncedDataSourceWasAccessibleException('test_component',
                                                            'test_source')
        data_for_alerting = []
        self.cosmos_network_alerting_factory.create_alerting_state(
            self.test_parent_id_1)

        # Generate first error alert
        self.cosmos_network_alerting_factory.classify_error_alert(
            test_err.code,
            cosmos_alerts.ErrorNoSyncedCosmosRestDataSourcesAlert,
            cosmos_alerts.SyncedCosmosRestDataSourcesFoundAlert,
            data_for_alerting, self.test_parent_id_1, self.test_parent_id_1,
            self.test_chain_name, datetime.now().timestamp(),
            AlertsMetricCode.NoSyncedCosmosRestSource.value, "error msg",
            "resolved msg", test_err.code
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Generate solved alert
        alerted_timestamp = datetime.now().timestamp() + 10
        self.cosmos_network_alerting_factory.classify_error_alert(
            test_err.code,
            cosmos_alerts.ErrorNoSyncedCosmosRestDataSourcesAlert,
            cosmos_alerts.SyncedCosmosRestDataSourcesFoundAlert,
            data_for_alerting, self.test_parent_id_1, self.test_parent_id_1,
            self.test_chain_name, alerted_timestamp,
            AlertsMetricCode.NoSyncedCosmosRestSource.value, "error msg",
            "resolved msg", code
        )

        expected_alert = cosmos_alerts.SyncedCosmosRestDataSourcesFoundAlert(
            self.test_chain_name, 'resolved msg', 'INFO', alerted_timestamp,
            self.test_parent_id_1, self.test_parent_id_1)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])
