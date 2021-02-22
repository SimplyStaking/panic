import logging
import unittest
from unittest import mock

from opsgenie_sdk import SuccessResponse

from src.alerter.alerts.system_alerts import (
    OpenFileDescriptorsIncreasedAboveThresholdAlert)
from src.channels_manager.apis.opsgenie_api import OpsgenieApi
from src.channels_manager.channels.opsgenie import OpsgenieChannel
from src.utils.data import RequestStatus
from src.utils.types import OpsgenieSeverities


class TestOpsgenieChannel(unittest.TestCase):
    def setUp(self) -> None:
        self.test_channel_name = 'test_opgenie_channel'
        self.test_channel_id = 'test_opsgenie_id12345'
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.test_api_key = 'test api key'

        self.test_opsgenie_api = OpsgenieApi(self.test_api_key, True)
        self.test_opsgenie_channel = OpsgenieChannel(self.test_channel_name,
                                                     self.test_channel_id,
                                                     self.dummy_logger,
                                                     self.test_opsgenie_api)

        self.test_system_name = 'test_system'
        self.test_percentage_usage = 50
        self.test_panic_severity = 'WARNING'
        self.test_last_monitored = 45
        self.test_parent_id = 'parent_1234'
        self.test_system_id = 'system_id32423'
        self.test_alert = OpenFileDescriptorsIncreasedAboveThresholdAlert(
            self.test_system_name, self.test_percentage_usage,
            self.test_panic_severity, self.test_last_monitored,
            self.test_panic_severity, self.test_parent_id, self.test_system_id
        )

    def tearDown(self) -> None:
        self.dummy_logger = None
        self.test_opsgenie_api = None
        self.test_opsgenie_channel = None
        self.test_alert = None

    def test__str__returns_channel_name(self) -> None:
        self.assertEqual(self.test_channel_name,
                         str(self.test_opsgenie_channel))

    def test_channel_name_returns_channel_name(self) -> None:
        self.assertEqual(self.test_channel_name,
                         self.test_opsgenie_channel.channel_name)

    def test_channel_id_returns_channel_id(self) -> None:
        self.assertEqual(self.test_channel_id,
                         self.test_opsgenie_channel.channel_id)

    def test_logger_returns_logger(self) -> None:
        self.assertEqual(self.dummy_logger, self.test_opsgenie_channel.logger)

    def test__init__initialised_opsgenie_api_correctly(self) -> None:
        self.assertEqual(self.test_opsgenie_api.__dict__,
                         self.test_opsgenie_channel._opsgenie_api.__dict__)

    @mock.patch.object(OpsgenieApi, "create_alert")
    def test_alert_triggers_an_alert_correctly(self, mock_create_alert) -> None:
        # In this test we will check that OpsgenieApi.create_alert() is called
        # with the correct parameters.
        expected_msg = "PANIC - {}".format(self.test_alert.alert_code.name)
        self.test_opsgenie_channel.alert(self.test_alert)
        mock_create_alert.assert_called_once_with(
            expected_msg, self.test_alert.message, OpsgenieSeverities.WARNING,
            self.test_alert.origin_id, self.test_alert.timestamp,
            alias=self.test_alert.alert_code.value)

    @mock.patch.object(OpsgenieApi, "create_alert")
    def test_alert_returns_success_if_create_alert_request_successful(
            self, mock_create_alert) -> None:
        mock_create_alert.return_value = SuccessResponse(
            request_id='id1', api_client=self.test_opsgenie_api._client)
        actual_ret = self.test_opsgenie_channel.alert(self.test_alert)
        self.assertEqual(RequestStatus.SUCCESS, actual_ret)

    @mock.patch.object(OpsgenieApi, "create_alert")
    def test_alert_returns_failed_if_create_alert_request_fails(
            self, mock_create_alert) -> None:
        mock_create_alert.return_value = 'This is not a SuccessResponse object'
        actual_ret = self.test_opsgenie_channel.alert(self.test_alert)
        self.assertEqual(RequestStatus.FAILED, actual_ret)

    @mock.patch.object(OpsgenieApi, "create_alert")
    def test_alert_returns_failed_if_create_alert_exception(
            self, mock_create_alert) -> None:
        mock_create_alert.side_effect = Exception('test')
        actual_ret = self.test_opsgenie_channel.alert(self.test_alert)
        self.assertEqual(RequestStatus.FAILED, actual_ret)
