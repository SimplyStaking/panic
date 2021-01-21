import logging
import unittest
import copy
from datetime import timedelta
from queue import Queue
from unittest import mock

from src.configs.system_alerts import SystemAlertsConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.alerter.alerters.system import SystemAlerter
from src.alerter.alerts.system_alerts import SystemStorageUsageIncreasedAboveThresholdAlert
from src.utils.constants import RAW_DATA_EXCHANGE, HEALTH_CHECK_EXCHANGE, \
    ALERT_EXCHANGE
from src.utils.env import ALERTER_PUBLISHING_QUEUE_SIZE


class TestSystemAlerter(unittest.TestCase):
    def setUp(self) -> None:
        self.dummy_logger = logging.getLogger('Dummy')
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbitmq = RabbitMQApi(self.dummy_logger,
                                    connection_check_time_interval=self.connection_check_time_interval)
        self.alerter_name = 'test_alerter'
        self.system_id = 'test_system_id'
        self.parent_id = 'test_parent_id'
        self.system_name = 'test_system'
        self.last_monitored = 1611143244.145402

        self.publishing_queue = Queue(ALERTER_PUBLISHING_QUEUE_SIZE)
        self.test_queue_name = 'test_alerter_queue'
        self.test_routing_key = 'test_alert_router.system'

        """
        ############# Alerts config base configuration ##########################
        """
        self.enabled_alert = "True"
        self.critical_threshold_percentage = 95
        self.critical_threshold_seconds = 200
        self.critical_repeat_seconds = 300
        self.critical_enabled = "True"
        self.warning_threshold_percentage = 85
        self.warning_threshold_seconds = 200
        self.warning_enabled = "True"

        self.base_config = {
            "name": "base_percent_config",
            "enabled": self.enabled_alert,
            "parent_id": self.parent_id,
            "critical_threshold": self.critical_threshold_percentage,
            "critical_repeat": self.critical_repeat_seconds,
            "critical_enabled": self.critical_enabled,
            "warning_threshold": self.warning_threshold_percentage,
            "warning_enabled": self.warning_enabled
        }

        self.open_file_descriptors = copy.deepcopy(self.base_config)
        self.open_file_descriptors['name'] = "open_file_descriptors"

        self.system_cpu_usage = copy.deepcopy(self.base_config)
        self.system_cpu_usage['name'] = "system_cpu_usage"

        self.system_storage_usage = copy.deepcopy(self.base_config)
        self.system_storage_usage['name'] = "system_storage_usage"

        self.system_ram_usage = copy.deepcopy(self.base_config)
        self.system_ram_usage['name'] = "system_ram_usage"

        self.system_is_down = copy.deepcopy(self.base_config)
        self.system_is_down['name'] = "system_is_down"
        self.system_is_down['critical_threshold'] = self.critical_threshold_seconds
        self.system_is_down['warning_threshold'] = self.warning_threshold_seconds

        self.system_alerts_config = SystemAlertsConfig(
            self.parent_id,
            self.open_file_descriptors,
            self.system_cpu_usage,
            self.system_storage_usage,
            self.system_ram_usage,
            self.system_is_down
        )
        self.test_system_alerter = SystemAlerter(
            self.alerter_name,
            self.system_alerts_config,
            self.dummy_logger
        )

        """
        ################# Metrics Received from Data Transformer #####################
        """
        self.warning = "WARNING"
        self.info = "INFO"
        self.critical = "CRITICAL"
        self.none = None
        # Process CPU Seconds Total
        self.current_cpu_sec = 42420.88
        self.previous_cpu_sec = 42400.42
        # Process Memory Usage
        self.current_mem_use = 20.00
        self.previous_mem_use = 10.23
        # Virtual Memory Usage
        self.current_v_mem_use = 735047680.0
        self.previous_v_mem_use = 723312578.0
        self.percent_usage = 40

        self.data_received_initially_no_alert = {
            "result": {
                "meta_data": {
                    "system_name": self.system_name,
                    "system_id": self.system_id,
                    "system_parent_id": self.parent_id,
                    "last_monitored": self.last_monitored
                },
                "data": {
                    "process_cpu_seconds_total": {
                        "current": self.current_cpu_sec,
                        "previous": self.none
                    },
                    "process_memory_usage": {
                        "current": self.current_mem_use,
                        "previous": self.none
                    },
                    "virtual_memory_usage": {
                        "current": self.current_v_mem_use,
                        "previous": self.none
                    },
                    "open_file_descriptors": {
                        "current": self.percent_usage,
                        "previous": self.none
                    },
                    "system_cpu_usage": {
                        "current": self.percent_usage,
                        "previous": self.none
                    },
                    "system_ram_usage": {
                        "current": self.percent_usage,
                        "previous": self.none
                    },
                    "system_storage_usage": {
                        "current": self.percent_usage,
                        "previous": self.none
                    },
                    "network_receive_bytes_total": {
                        "current": self.none,
                        "previous": self.none,
                    },
                    "network_transmit_bytes_total": {
                        "current": self.none,
                        "previous": self.none
                    },
                    "disk_io_time_seconds_total": {
                        "current": self.none,
                        "previous": self.none,
                    },
                    "network_transmit_bytes_per_second": {
                        "current": self.none,
                        "previous": self.none,
                    },
                    "network_receive_bytes_per_second": {
                        "current": self.none,
                        "previous": self.none
                    },
                    "disk_io_time_seconds_in_interval": {
                        "current": self.none,
                        "previous": self.none,
                    },
                    "went_down_at": {
                        "current": self.none,
                        "previous": self.none
                    }
                }
            }
        }

        self.data_received_initially_warning_alert = \
            copy.deepcopy(self.data_received_initially_no_alert)

        self.data_received_initially_warning_alert[
            'result']['data']['open_file_descriptors']['current'] = self.percent_usage + 46
        self.data_received_initially_warning_alert[
            'result']['data']['system_cpu_usage']['current'] = self.percent_usage + 46
        self.data_received_initially_warning_alert[
            'result']['data']['system_ram_usage']['current'] = self.percent_usage + 46
        self.data_received_initially_warning_alert[
            'result']['data']['system_storage_usage']['current'] = self.percent_usage + 46

        self.data_received_below_warning_threshold = \
            copy.deepcopy(self.data_received_initially_no_alert)

        self.data_received_below_warning_threshold[
            'result']['data']['open_file_descriptors']['previous'] = self.percent_usage + 46
        self.data_received_below_warning_threshold[
            'result']['data']['system_cpu_usage']['previous'] = self.percent_usage + 46
        self.data_received_below_warning_threshold[
            'result']['data']['system_ram_usage']['previous'] = self.percent_usage + 46
        self.data_received_below_warning_threshold[
            'result']['data']['system_storage_usage']['previous'] = self.percent_usage + 46

        self.data_received_initially_critical_alert = \
            copy.deepcopy(self.data_received_initially_no_alert)

        self.data_received_initially_critical_alert[
            'result']['data']['open_file_descriptors']['current'] = self.percent_usage + 56
        self.data_received_initially_critical_alert[
            'result']['data']['system_cpu_usage']['current'] = self.percent_usage + 56
        self.data_received_initially_critical_alert[
            'result']['data']['system_ram_usage']['current'] = self.percent_usage + 56
        self.data_received_initially_critical_alert[
            'result']['data']['system_storage_usage']['current'] = self.percent_usage + 56

        self.data_received_below_critical_above_warning = \
            copy.deepcopy(self.data_received_initially_warning_alert)

        self.data_received_below_critical_above_warning[
            'result']['data']['open_file_descriptors']['previous'] = self.percent_usage + 56
        self.data_received_below_critical_above_warning[
            'result']['data']['system_cpu_usage']['previous'] = self.percent_usage + 56
        self.data_received_below_critical_above_warning[
            'result']['data']['system_ram_usage']['previous'] = self.percent_usage + 56
        self.data_received_below_critical_above_warning[
            'result']['data']['system_storage_usage']['previous'] = self.percent_usage + 56

    def tearDown(self) -> None:
        self.dummy_logger = None
        self.rabbitmq = None
        self.system_alerts_config = None
        self.test_system_alerter = None
        self.publishing_queue = None

    def test_returns_alerter_name_as_str(self) -> None:
        self.assertEqual(self.alerter_name, self.test_system_alerter.__str__())

    def test_returns_alerter_name(self) -> None:
        self.assertEqual(self.alerter_name, self.test_system_alerter.alerter_name)

    def test_returns_logger(self) -> None:
        self.assertEqual(self.dummy_logger, self.test_system_alerter.logger)

    def test_returns_publishing_queue_size(self) -> None:
        self.assertEqual(self.publishing_queue.qsize(), self.test_system_alerter.publishing_queue.qsize())

    def test_returns_alerts_configs_from_alerter(self) -> None:
        self.assertEqual(self.system_alerts_config, self.test_system_alerter.alerts_configs)

    """
    ###################### Tests without using RabbitMQ ############################
    """
    @mock.patch.object(SystemAlerter, "_classify_alert")
    def test_alerts_initial_run_no_alerts_count_classify_alert(
            self, mock_classify_alert) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            self.assertEqual(4, mock_classify_alert.call_count)
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert", autospec=True)
    def test_open_file_descriptors_initial_run_no_increase_alerts(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert", autospec=True)
    def test_open_file_descriptors_initial_run_no_decrease_alerts(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_cpu_usage_initial_run_no_increase_alerts(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_system_cpu_usage_initial_run_no_decrease_alerts(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_ram_usage_initial_run_no_increase_alerts(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_system_ram_usage_initial_run_no_decrease_alerts(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_storage_usage_initial_run_no_increase_alerts(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_system_storage_usage_initial_run_no_decrease_alerts(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert", autospec=True)
    def test_open_file_descriptors_initial_run_no_increase_alerts_then_no_increase_alerts(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert", autospec=True)
    def test_open_file_descriptors_initial_run_no_decrease_alerts_then_no_decrease_alerts(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_cpu_usage_initial_run_no_increase_alerts_then_no_increase_alerts(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_system_cpu_usage_initial_run_no_decrease_then_no_decrease_alerts(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_ram_usage_initial_run_no_increase_alerts_then_no_increase_alerts(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_system_ram_usage_initial_run_no_decrease_alerts_then_no_decrease_alerts(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_storage_usage_initial_run_no_increase_alerts_then_no_increase_alerts(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_system_storage_usage_initial_run_no_decrease_alerts_then_no_decrease_alerts(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_all_alerts_classification_no_alerts_then_no_alerts(
            self, mock_system_storage_usage_decrease,
            mock_system_ram_usage_decrease, mock_cpu_usage_decrease,
            mock_open_file_usage_decrease, mock_system_storage_usage_increase,
            mock_system_ram_usage_increase, mock_cpu_usage_increase,
            mock_open_file_usage_increase) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_system_storage_usage_increase.assert_not_called()
            mock_system_ram_usage_increase.assert_not_called()
            mock_cpu_usage_increase.assert_not_called()
            mock_open_file_usage_increase.assert_not_called()
            mock_system_storage_usage_decrease.assert_not_called()
            mock_system_ram_usage_decrease.assert_not_called()
            mock_cpu_usage_decrease.assert_not_called()
            mock_open_file_usage_decrease.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_system_storage_usage_increase.assert_not_called()
            mock_system_ram_usage_increase.assert_not_called()
            mock_cpu_usage_increase.assert_not_called()
            mock_open_file_usage_increase.assert_not_called()
            mock_system_storage_usage_decrease.assert_not_called()
            mock_system_ram_usage_decrease.assert_not_called()
            mock_cpu_usage_decrease.assert_not_called()
            mock_open_file_usage_decrease.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert", autospec=True)
    def test_open_file_descriptors_initial_run_no_increase_alerts_then_warning_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['open_file_descriptors']['current'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['open_file_descriptors']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert", autospec=True)
    def test_open_file_descriptors_initial_run_no_decrease_alerts_then_no_decrease_alerts_on_warning_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['open_file_descriptors']['current'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_cpu_usage_initial_run_no_increase_alerts_then_warning_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_cpu_usage']['current'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_cpu_usage']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_system_cpu_usage_initial_run_no_decrease_then_no_decrease_alerts_on_warning_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_cpu_usage']['current'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_ram_usage_initial_run_no_increase_alerts_then_warning_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_ram_usage']['current'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_ram_usage']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_system_ram_usage_initial_run_no_decrease_alerts_then_no_decrease_alerts_on_warning_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_ram_usage']['current'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_storage_usage_initial_run_no_increase_alerts_then_warning_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_storage_usage']['current'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_storage_usage']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_system_storage_usage_initial_run_no_decrease_alerts_then_no_decrease_alerts_on_warning_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_storage_usage']['current'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_alerts_classification_run_no_alerts_then_warning_alerts(
            self, mock_system_storage_usage_decrease,
            mock_system_ram_usage_decrease, mock_cpu_usage_decrease,
            mock_open_file_usage_decrease, mock_system_storage_usage_increase,
            mock_system_ram_usage_increase, mock_cpu_usage_increase,
            mock_open_file_usage_increase) -> None:

        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_system_storage_usage_increase.assert_not_called()
            mock_system_ram_usage_increase.assert_not_called()
            mock_cpu_usage_increase.assert_not_called()
            mock_open_file_usage_increase.assert_not_called()
            mock_system_storage_usage_decrease.assert_not_called()
            mock_system_ram_usage_decrease.assert_not_called()
            mock_cpu_usage_decrease.assert_not_called()
            mock_open_file_usage_decrease.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data = self.data_received_initially_warning_alert['result']['data']
        meta_data = self.data_received_initially_warning_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_system_storage_usage_increase.assert_called_once_with(
                self.system_name, data['system_storage_usage']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            mock_system_ram_usage_increase.assert_called_once_with(
                self.system_name, data['system_ram_usage']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            mock_cpu_usage_increase.assert_called_once_with(
                self.system_name, data['system_cpu_usage']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            mock_open_file_usage_increase.assert_called_once_with(
                self.system_name, data['open_file_descriptors']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            mock_system_storage_usage_decrease.assert_not_called()
            mock_system_ram_usage_decrease.assert_not_called()
            mock_cpu_usage_decrease.assert_not_called()
            mock_open_file_usage_decrease.assert_not_called()
            self.assertEqual(4, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert", autospec=True)
    def test_open_file_descriptors_initial_run_no_increase_alerts_then_critical_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['open_file_descriptors']['current'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['open_file_descriptors']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert", autospec=True)
    def test_open_file_descriptors_initial_run_no_decrease_alerts_then_no_decrease_alerts_on_critical_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['open_file_descriptors']['current'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_cpu_usage_initial_run_no_increase_alerts_then_critical_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_cpu_usage']['current'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_cpu_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_system_cpu_usage_initial_run_no_decrease_then_no_decrease_alerts_on_critical_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_cpu_usage']['current'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_ram_usage_initial_run_no_increase_alerts_then_critical_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_ram_usage']['current'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_ram_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_system_ram_usage_initial_run_no_decrease_alerts_then_no_decrease_alerts_on_critical_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_ram_usage']['current'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_storage_usage_initial_run_no_increase_alerts_then_critical_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_storage_usage']['current'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_storage_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_system_storage_usage_initial_run_no_decrease_alerts_then_no_decrease_alerts_on_critical_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_storage_usage']['current'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_alerts_classification_run_no_alerts_then_critical_alerts(
            self, mock_system_storage_usage_decrease,
            mock_system_ram_usage_decrease, mock_cpu_usage_decrease,
            mock_open_file_usage_decrease, mock_system_storage_usage_increase,
            mock_system_ram_usage_increase, mock_cpu_usage_increase,
            mock_open_file_usage_increase) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_system_storage_usage_increase.assert_not_called()
            mock_system_ram_usage_increase.assert_not_called()
            mock_cpu_usage_increase.assert_not_called()
            mock_open_file_usage_increase.assert_not_called()
            mock_system_storage_usage_decrease.assert_not_called()
            mock_system_ram_usage_decrease.assert_not_called()
            mock_cpu_usage_decrease.assert_not_called()
            mock_open_file_usage_decrease.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data = self.data_received_initially_critical_alert['result']['data']
        meta_data = self.data_received_initially_critical_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_system_storage_usage_increase.assert_called_once_with(
                self.system_name, data['system_storage_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            mock_system_ram_usage_increase.assert_called_once_with(
                self.system_name, data['system_ram_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            mock_cpu_usage_increase.assert_called_once_with(
                self.system_name, data['system_cpu_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            mock_open_file_usage_increase.assert_called_once_with(
                self.system_name, data['open_file_descriptors']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            mock_system_storage_usage_decrease.assert_not_called()
            mock_system_ram_usage_decrease.assert_not_called()
            mock_cpu_usage_decrease.assert_not_called()
            mock_open_file_usage_decrease.assert_not_called()
            self.assertEqual(4, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(SystemAlerter, "_classify_alert")
    def test_alerts_initial_run_warning_alerts_count_classify_alert(
            self, mock_classify_alert) -> None:
        data_for_alerting = []
        data = self.data_received_initially_warning_alert['result']['data']
        meta_data = self.data_received_initially_warning_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            self.assertEqual(4, mock_classify_alert.call_count)
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert", autospec=True)
    def test_open_file_descriptors_initial_run_warning_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['open_file_descriptors']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['open_file_descriptors']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert", autospec=True)
    def test_open_file_descriptors_initial_run_no_decrease_alerts_on_warning_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['open_file_descriptors']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_cpu_usage_initial_run_warning_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_cpu_usage']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_cpu_usage']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_system_cpu_usage_initial_run_no_decrease_alerts_on_warning_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_cpu_usage']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_ram_usage_initial_run_warning_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_ram_usage']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_ram_usage']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_system_ram_usage_initial_run_no_decrease_alerts_on_warning_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_ram_usage']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_storage_usage_initial_run_warning_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_storage_usage']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_storage_usage']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_system_storage_usage_initial_run_no_decrease_alerts_on_warning_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_storage_usage']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_alerts_initial_run_warning_alerts_count_alerts(
            self, mock_system_storage_usage_decrease,
            mock_system_ram_usage_decrease, mock_cpu_usage_decrease,
            mock_open_file_usage_decrease, mock_system_storage_usage_increase,
            mock_system_ram_usage_increase, mock_cpu_usage_increase,
            mock_open_file_usage_increase) -> None:
        data_for_alerting = []
        data = self.data_received_initially_warning_alert['result']['data']
        meta_data = self.data_received_initially_warning_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_system_storage_usage_increase.assert_called_once_with(
                self.system_name, data['system_storage_usage']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            mock_system_ram_usage_increase.assert_called_once_with(
                self.system_name, data['system_ram_usage']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            mock_cpu_usage_increase.assert_called_once_with(
                self.system_name, data['system_cpu_usage']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            mock_open_file_usage_increase.assert_called_once_with(
                self.system_name, data['open_file_descriptors']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            mock_system_storage_usage_decrease.assert_not_called()
            mock_system_ram_usage_decrease.assert_not_called()
            mock_cpu_usage_decrease.assert_not_called()
            mock_open_file_usage_decrease.assert_not_called()
            self.assertEqual(4, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert", autospec=True)
    def test_open_file_descriptors_initial_run_warning_alert_then_no_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['open_file_descriptors']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['open_file_descriptors']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['open_file_descriptors']['current'] = self.percent_usage + 36
        data['open_file_descriptors']['previous'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['open_file_descriptors']['previous'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert", autospec=True)
    def test_open_file_descriptors_initial_run_warning_alert_then_info_alert_on_decrease(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['open_file_descriptors']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['open_file_descriptors']['current'] = self.percent_usage + 36
        data['open_file_descriptors']['previous'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['open_file_descriptors']['current'],
                self.info, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_cpu_usage_initial_run_warning_alert_then_no_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_cpu_usage']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_cpu_usage']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_cpu_usage']['current'] = self.percent_usage + 36
        data['system_cpu_usage']['previous'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_cpu_usage']['previous'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_system_cpu_usage_initial_run_warning_alert_then_info_alert_on_decrease(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_cpu_usage']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_cpu_usage']['current'] = self.percent_usage + 36
        data['system_cpu_usage']['previous'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_cpu_usage']['current'],
                self.info, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_ram_usage_initial_run_warning_alert_then_no_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_ram_usage']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_ram_usage']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_ram_usage']['current'] = self.percent_usage + 36
        data['system_ram_usage']['previous'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_ram_usage']['previous'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_system_ram_usage_initial_run_warning_alert_then_info_alerts_on_decrease(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_ram_usage']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_ram_usage']['current'] = self.percent_usage + 36
        data['system_ram_usage']['previous'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_ram_usage']['current'],
                self.info, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_storage_usage_initial_run_warning_alert_then_no_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_storage_usage']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_storage_usage']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_storage_usage']['current'] = self.percent_usage + 36
        data['system_storage_usage']['previous'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_storage_usage']['previous'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_system_storage_usage_initial_run_warning_alert_then_info_alert_on_decrease(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_storage_usage']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_storage_usage']['current'] = self.percent_usage + 36
        data['system_storage_usage']['previous'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_storage_usage']['current'],
                self.info, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert", autospec=True)
    def test_open_file_descriptors_initial_run_warning_alerts_then_critical_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['open_file_descriptors']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['open_file_descriptors']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['open_file_descriptors']['current'] = self.percent_usage + 56
        data['open_file_descriptors']['previous'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_with(
                self.system_name, data['open_file_descriptors']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert", autospec=True)
    def test_open_file_descriptors_initial_run_no_decrease_alerts_on_warning_alert_then_no_decrease_alerts_on_critical_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['open_file_descriptors']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['open_file_descriptors']['current'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_cpu_usage_initial_run_warning_alert_then_critical_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_cpu_usage']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_cpu_usage']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_cpu_usage']['current'] = self.percent_usage + 56
        data['system_cpu_usage']['previous'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_with(
                self.system_name, data['system_cpu_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_system_cpu_usage_initial_run_no_decrease_on_warning_then_no_decrease_alerts_on_critical_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_cpu_usage']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_cpu_usage']['current'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_ram_usage_initial_run_warning_alert_then_critical_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_ram_usage']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_ram_usage']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_ram_usage']['current'] = self.percent_usage + 56
        data['system_ram_usage']['previous'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_with(
                self.system_name, data['system_ram_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_system_ram_usage_initial_run_no_decrease_alerts_on_warning_then_no_decrease_alerts_on_critical_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_ram_usage']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_ram_usage']['current'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_storage_usage_initial_run_warning_alert_then_critical_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_storage_usage']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_storage_usage']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_storage_usage']['current'] = self.percent_usage + 56
        data['system_storage_usage']['previous'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_with(
                self.system_name, data['system_storage_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_system_storage_usage_initial_run_no_decrease_alerts_on_warning_then_no_decrease_alerts_on_critical_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_storage_usage']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_storage_usage']['current'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_alerts_above_warning_threshold_then_below_warning(
            self, mock_system_storage_usage_decrease,
            mock_system_ram_usage_decrease, mock_cpu_usage_decrease,
            mock_open_file_usage_decrease, mock_system_storage_usage_increase,
            mock_system_ram_usage_increase, mock_cpu_usage_increase,
            mock_open_file_usage_increase) -> None:
        data_for_alerting = []
        data = self.data_received_initially_warning_alert['result']['data']
        meta_data = self.data_received_initially_warning_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_system_storage_usage_increase.assert_called_once_with(
                self.system_name, data['system_storage_usage']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            mock_system_ram_usage_increase.assert_called_once_with(
                self.system_name, data['system_ram_usage']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            mock_cpu_usage_increase.assert_called_once_with(
                self.system_name, data['system_cpu_usage']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            mock_open_file_usage_increase.assert_called_once_with(
                self.system_name, data['open_file_descriptors']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(4, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data_for_alerting = []
        data = self.data_received_below_warning_threshold['result']['data']
        meta_data = self.data_received_below_warning_threshold['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_system_storage_usage_decrease.assert_called_once_with(
                self.system_name, data['system_storage_usage']['current'],
                self.info, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            mock_system_ram_usage_decrease.assert_called_once_with(
                self.system_name, data['system_ram_usage']['current'],
                self.info, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            mock_cpu_usage_decrease.assert_called_once_with(
                self.system_name, data['system_cpu_usage']['current'],
                self.info, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            mock_open_file_usage_decrease.assert_called_once_with(
                self.system_name, data['open_file_descriptors']['current'],
                self.info, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(4, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_alerts_initial_run_above_critical_threshold(
            self, mock_system_storage_usage, mock_system_ram_usage,
            mock_cpu_usage, mock_open_file_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_critical_alert['result']['data']
        meta_data = self.data_received_initially_critical_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_system_storage_usage.assert_called_once_with(
                self.system_name, data['system_storage_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            mock_system_ram_usage.assert_called_once_with(
                self.system_name, data['system_ram_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            mock_cpu_usage.assert_called_once_with(
                self.system_name, data['system_cpu_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            mock_open_file_usage.assert_called_once_with(
                self.system_name, data['open_file_descriptors']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(4, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_alerts_above_critical_threshold_then_between_critical_and_warning(
            self, mock_system_storage_usage_decrease,
            mock_system_ram_usage_decrease, mock_cpu_usage_decrease,
            mock_open_file_usage_decrease, mock_system_storage_usage_increase,
            mock_system_ram_usage_increase, mock_cpu_usage_increase,
            mock_open_file_usage_increase) -> None:
        data_for_alerting = []
        data = self.data_received_initially_critical_alert['result']['data']
        meta_data = self.data_received_initially_critical_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_system_storage_usage_increase.assert_called_once_with(
                self.system_name, data['system_storage_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            mock_system_ram_usage_increase.assert_called_once_with(
                self.system_name, data['system_ram_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            mock_cpu_usage_increase.assert_called_once_with(
                self.system_name, data['system_cpu_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            mock_open_file_usage_increase.assert_called_once_with(
                self.system_name, data['open_file_descriptors']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(4, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data_for_alerting = []
        data = self.data_received_below_critical_above_warning['result']['data']
        meta_data = self.data_received_below_critical_above_warning['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data, data_for_alerting)
        try:
            mock_system_storage_usage_decrease.assert_called_once_with(
                self.system_name, data['system_storage_usage']['current'],
                self.info, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            mock_system_ram_usage_decrease.assert_called_once_with(
                self.system_name, data['system_ram_usage']['current'],
                self.info, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            mock_cpu_usage_decrease.assert_called_once_with(
                self.system_name, data['system_cpu_usage']['current'],
                self.info, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            mock_open_file_usage_decrease.assert_called_once_with(
                self.system_name, data['open_file_descriptors']['current'],
                self.info, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(4, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

