import unittest
from datetime import datetime
from unittest import mock

import opsgenie_sdk
from parameterized import parameterized

from src.alerter.alerts.system_alerts import (
    OpenFileDescriptorsIncreasedAboveThresholdAlert)
from src.channels_manager.apis.opsgenie_api import OpsgenieApi
from src.utils.types import OpsgenieSeverities


class TestOpsgenieApi(unittest.TestCase):
    def setUp(self) -> None:
        self.test_api_key = 'test api key'
        self.test_eu_host_true = True
        self.test_eu_host_false = False
        self.test_system_name = 'test system'
        self.test_percentage_usage = 50
        self.test_panic_severity = 'WARNING'
        self.test_last_monitored = 45.5
        self.test_parent_id = 'chain123'
        self.test_system_id = 'system123'
        self.test_alert = OpenFileDescriptorsIncreasedAboveThresholdAlert(
            self.test_system_name, self.test_percentage_usage,
            self.test_panic_severity, self.test_last_monitored,
            self.test_panic_severity, self.test_parent_id, self.test_system_id
        )
        self.test_opsgenie_severity = OpsgenieSeverities.WARNING
        self.test_alias = self.test_alert.alert_code.value

        self.test_alert_create_payload = opsgenie_sdk.CreateAlertPayload(
            message=self.test_alert.alert_code.name,
            description="Message: {} \n Triggered at: {}".format(
                self.test_alert.message, datetime.fromtimestamp(
                    self.test_alert.timestamp)),
            priority=self.test_opsgenie_severity.value,
            source=self.test_alert.origin_id, alias=self.test_alias
        )

        self.test_opsgenie_api_eu = OpsgenieApi(self.test_api_key,
                                                self.test_eu_host_true)
        self.test_opsgenie_api_non_eu = OpsgenieApi(self.test_api_key,
                                                    self.test_eu_host_false)

    def tearDown(self) -> None:
        self.test_opsgenie_api_eu = None
        self.test_opsgenie_api_non_eu = None
        self.test_alert = None
        self.test_alert_create_payload = None

    @parameterized.expand([(True,), (False,), ])
    def test__init__creates_a_correct_opsgenie_api_instance(self,
                                                            eu_host) -> None:
        # We will parametrize this test to check that the initialization is
        # correct for both eu hosts and non-eu hosts. We can only check that
        # OpsgenieApi._client and OpsgenieApi._alert_api were instantiated with
        # the correct configuration as __eq__ was not implemented for them.
        expected_api_configuration = opsgenie_sdk.configuration.Configuration()
        expected_api_configuration.api_key['Authorization'] = self.test_api_key
        expected_api_configuration.host = "https://api.eu.opsgenie.com" if \
            eu_host else "https://api.opsgenie.com"

        opsgenie_api = self.test_opsgenie_api_eu if eu_host else \
            self.test_opsgenie_api_non_eu

        self.assertEqual(expected_api_configuration.__dict__,
                         opsgenie_api._client.configuration.__dict__)
        self.assertEqual(
            expected_api_configuration.__dict__,
            opsgenie_api._alert_api.api_client.configuration.__dict__)

    """
    In the tests below we will only check that the opsgenie_sdk functions are 
    called correctly and that the call's response is returned. This is done 
    because we cannot test whether the actual operation was successful without 
    exposing infrastructure details. Note we will parameterize these tests so 
    that we can test for both eu and non-eu hosts
    """

    @parameterized.expand([
        ('self.test_opsgenie_api_eu',),
        ('self.test_opsgenie_api_non_eu',),
    ])
    @mock.patch.object(opsgenie_sdk.AlertApi, "create_alert")
    def test_create_alert_triggers_an_alert_correctly(
            self, opsgenie_api, mock_create_alert) -> None:
        opsgenie_api = eval(opsgenie_api)
        mock_create_alert.return_value = opsgenie_sdk.SuccessResponse

        ret = opsgenie_api.create_alert(
            self.test_alert.alert_code.name, self.test_alert.message,
            self.test_opsgenie_severity, self.test_alert.origin_id,
            self.test_alert.timestamp, self.test_alias)

        mock_create_alert.assert_called_once_with(
            create_alert_payload=self.test_alert_create_payload)
        self.assertEqual(ret, opsgenie_sdk.SuccessResponse)

    @parameterized.expand([
        ('self.test_opsgenie_api_eu',),
        ('self.test_opsgenie_api_non_eu',),
    ])
    @mock.patch.object(opsgenie_sdk.AlertApi, "close_alert")
    def test_close_alert_closes_an_alert_correctly(
            self, opsgenie_api, mock_close_alert) -> None:
        opsgenie_api = eval(opsgenie_api)
        mock_close_alert.return_value = opsgenie_sdk.SuccessResponse
        expected_payload = opsgenie_sdk.CloseAlertPayload()

        ret = opsgenie_api.close_alert(self.test_alias)

        mock_close_alert.assert_called_once_with(
            identifier=self.test_alias,
            close_alert_payload=expected_payload)
        self.assertEqual(ret, opsgenie_sdk.SuccessResponse)

    @parameterized.expand([
        ('self.test_opsgenie_api_eu',),
        ('self.test_opsgenie_api_non_eu',),
    ])
    @mock.patch.object(opsgenie_sdk.AlertApi, "update_alert_priority")
    def test_update_severity_updates_alert_priority_correctly(
            self, opsgenie_api, mock_update_priority) -> None:
        opsgenie_api = eval(opsgenie_api)
        mock_update_priority.return_value = opsgenie_sdk.SuccessResponse
        new_severity = OpsgenieSeverities.CRITICAL
        expected_payload = opsgenie_sdk.UpdateAlertPriorityPayload(
            priority=new_severity.value)

        ret = opsgenie_api.update_severity(new_severity, self.test_alias)

        mock_update_priority.assert_called_once_with(
            identifier=self.test_alias,
            update_alert_priority_payload=expected_payload)
        self.assertEqual(ret, opsgenie_sdk.SuccessResponse)

    @parameterized.expand([
        ('self.test_opsgenie_api_eu',),
        ('self.test_opsgenie_api_non_eu',),
    ])
    @mock.patch.object(opsgenie_sdk.AlertApi, "update_alert_message")
    def test_update_message_updates_alert_message_correctly(
            self, opsgenie_api, mock_update_message) -> None:
        opsgenie_api = eval(opsgenie_api)
        mock_update_message.return_value = opsgenie_sdk.SuccessResponse
        new_message = 'This is a new alert message'
        expected_payload = opsgenie_sdk.UpdateAlertMessagePayload(
            message=new_message)

        ret = opsgenie_api.update_message(new_message, self.test_alias)

        mock_update_message.assert_called_once_with(
            identifier=self.test_alias,
            update_alert_message_payload=expected_payload)
        self.assertEqual(ret, opsgenie_sdk.SuccessResponse)

    @parameterized.expand([
        ('self.test_opsgenie_api_eu',),
        ('self.test_opsgenie_api_non_eu',),
    ])
    @mock.patch.object(opsgenie_sdk.AlertApi, "update_alert_description")
    def test_update_description_updates_alert_description_correctly(
            self, opsgenie_api, mock_update_description) -> None:
        opsgenie_api = eval(opsgenie_api)
        mock_update_description.return_value = opsgenie_sdk.SuccessResponse
        new_description = 'This is a new alert description'
        expected_payload = opsgenie_sdk.UpdateAlertDescriptionPayload(
            description=new_description)

        ret = opsgenie_api.update_description(new_description, self.test_alias)

        mock_update_description.assert_called_once_with(
            identifier=self.test_alias,
            update_alert_description_payload=expected_payload)
        self.assertEqual(ret, opsgenie_sdk.SuccessResponse)

    @parameterized.expand([
        ('self.test_opsgenie_api_eu',),
        ('self.test_opsgenie_api_non_eu',),
    ])
    @mock.patch.object(opsgenie_sdk.AlertApi, "get_request_status")
    def test_get_request_status_gets_request_status_correctly(
            self, opsgenie_api, mock_get_request_status) -> None:
        opsgenie_api = eval(opsgenie_api)
        mock_get_request_status.return_value = opsgenie_sdk.SuccessResponse
        request_id = 'req_id1234'

        ret = opsgenie_api.get_request_status(request_id)

        mock_get_request_status.assert_called_once_with(request_id=request_id)
        self.assertEqual(ret, opsgenie_sdk.SuccessResponse)
