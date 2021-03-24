import unittest
from datetime import datetime
from unittest import mock

from pdpyras import EventsAPISession

from src.alerter.alerts.system_alerts import (
    OpenFileDescriptorsIncreasedAboveThresholdAlert)
from src.channels_manager.apis.pagerduty_api import PagerDutyApi
from src.utils.types import PagerDutySeverities


class TestPagerDutyApi(unittest.TestCase):
    def setUp(self) -> None:
        self.test_integration_key = 'test_integration_key'

        self.test_pagerduty_api = PagerDutyApi(self.test_integration_key)

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
        self.test_dedup_key = 'test_dedup_key'
        self.test_pagerduty_severity = PagerDutySeverities.WARNING
        self.test_alert_payload = {
            'timestamp': datetime.fromtimestamp(
                self.test_alert.timestamp).isoformat()
        }

    def tearDown(self) -> None:
        self.test_pagerduty_api = None
        self.test_alert = None
        self.test_alert_payload = None

    def test__init__creates_a_correct_pagerduty_api_instance(self) -> None:
        # We cannot directly check the __dict__ of the pagerduty instance
        # because __eq__ was not implemented for some members
        self.assertEqual(self.test_integration_key,
                         self.test_pagerduty_api._session.api_key)
        self.assertEqual({'_session'},
                         set(self.test_pagerduty_api.__dict__.keys()))

    @mock.patch.object(EventsAPISession, "trigger")
    def test_trigger_creates_an_alert_successfully(self, mock_trigger) -> None:
        # In this test we will check that the EventsApiSession.trigger function
        # is called correctly, and that whatever the call returns is returned by
        # PagerDutyApi.trigger. Note that we will not check whether an alert is
        # really triggered because we cannot do so without exposing
        # infrastructure details
        mock_trigger.return_value = self.test_dedup_key

        ret = self.test_pagerduty_api.trigger(
            self.test_alert.message, self.test_pagerduty_severity,
            self.test_alert.origin_id, self.test_alert.timestamp,
            self.test_dedup_key)

        mock_trigger.assert_called_once_with(
            summary=self.test_alert.message, source=self.test_alert.origin_id,
            dedup_key=self.test_dedup_key,
            severity=self.test_pagerduty_severity.value,
            payload=self.test_alert_payload,
        )
        self.assertEqual(ret, self.test_dedup_key)
