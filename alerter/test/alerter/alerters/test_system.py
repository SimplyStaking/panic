import json
import logging
import unittest
import copy
import datetime
from queue import Queue
from unittest import mock

import pika
from freezegun import freeze_time

from src.alerter.alerts.system_alerts import OpenFileDescriptorsIncreasedAboveThresholdAlert
from src.configs.system_alerts import SystemAlertsConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.alerter.alerters.system import SystemAlerter
from src.utils.env import ALERTER_PUBLISHING_QUEUE_SIZE, RABBIT_IP
from src.utils.constants import ALERT_EXCHANGE, HEALTH_CHECK_EXCHANGE


class TestSystemAlerter(unittest.TestCase):
    def setUp(self) -> None:
        self.dummy_logger = logging.getLogger('Dummy')
        self.rabbit_ip = RABBIT_IP
        self.alert_input_exchange = ALERT_EXCHANGE
        self.connection_check_time_interval = datetime.timedelta(seconds=0)
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)

        self.alerter_name = 'test_alerter'
        self.system_id = 'test_system_id'
        self.parent_id = 'test_parent_id'
        self.system_name = 'test_system'
        self.last_monitored = 1611619200
        self.publishing_queue = Queue(ALERTER_PUBLISHING_QUEUE_SIZE)
        self.test_queue_name = 'test_alerter_queue'
        self.test_routing_key = 'test_alert_router.system'
        self.queue_used = "system_alerter_queue_" + self.parent_id
        self.target_queue_used = "alert_router_queue"
        self.routing_key = "alerter.system." + self.parent_id
        self.bad_routing_key = "alerter.system.not_real"
        self.alert_router_routing_key = 'alert_router.system'
        self.heartbeat_queue = 'heartbeat queue'

        self.heartbeat_test = {
            'component_name': self.alerter_name,
            'timestamp': datetime.datetime(2012, 1, 1, 1).timestamp()
        }

        """
        ############# Alerts config base configuration ######################
        """
        self.enabled_alert = "True"
        self.critical_threshold_percentage = 95
        self.critical_threshold_seconds = 300
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
        self.system_is_down['critical_threshold'] = \
            self.critical_threshold_seconds
        self.system_is_down['warning_threshold'] = \
            self.warning_threshold_seconds

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
        ############# Alerts config warning alerts disabled ######################
        """

        self.base_config['warning_enabled'] = str(not bool(self.warning_enabled))
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
        self.system_is_down['critical_threshold'] = \
            self.critical_threshold_seconds
        self.system_is_down['warning_threshold'] = \
            self.warning_threshold_seconds

        self.system_alerts_config_warnings_disabled = SystemAlertsConfig(
            self.parent_id,
            self.open_file_descriptors,
            self.system_cpu_usage,
            self.system_storage_usage,
            self.system_ram_usage,
            self.system_is_down
        )
        self.test_system_alerter_warnings_disabled = SystemAlerter(
            self.alerter_name,
            self.system_alerts_config_warnings_disabled,
            self.dummy_logger
        )

        """
        ############# Alerts config critical alerts disabled ######################
        """
        self.base_config['warning_enabled'] = self.warning_enabled
        self.base_config['critical_enabled'] = str(not bool(self.critical_enabled))
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
        self.system_is_down['critical_threshold'] = \
            self.critical_threshold_seconds
        self.system_is_down['warning_threshold'] = \
            self.warning_threshold_seconds

        self.system_alerts_config_critical_disabled = SystemAlertsConfig(
            self.parent_id,
            self.open_file_descriptors,
            self.system_cpu_usage,
            self.system_storage_usage,
            self.system_ram_usage,
            self.system_is_down
        )

        self.test_system_alerter_critical_disabled = SystemAlerter(
            self.alerter_name,
            self.system_alerts_config_critical_disabled,
            self.dummy_logger
        )

        """
        ############# Alerts config all alerts disabled ######################
        """
        self.base_config['warning_enabled'] = self.warning_enabled
        self.base_config['critical_enabled'] = self.critical_enabled
        self.base_config['enabled'] = str(not bool(self.enabled_alert))
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
        self.system_is_down['critical_threshold'] = \
            self.critical_threshold_seconds
        self.system_is_down['warning_threshold'] = \
            self.warning_threshold_seconds

        self.system_alerts_config_all_disabled = SystemAlertsConfig(
            self.parent_id,
            self.open_file_descriptors,
            self.system_cpu_usage,
            self.system_storage_usage,
            self.system_ram_usage,
            self.system_is_down
        )

        self.test_system_alerter_all_disabled = SystemAlerter(
            self.alerter_name,
            self.system_alerts_config_all_disabled,
            self.dummy_logger
        )

        """
        ################# Metrics Received from Data Transformer ############
        """
        self.warning = "WARNING"
        self.info = "INFO"
        self.critical = "CRITICAL"
        self.error = "ERROR"
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

        self.data_received_error_data = {
            "error": {
                "meta_data": {
                    "system_name": self.system_name,
                    "system_id": self.system_id,
                    "system_parent_id": self.parent_id,
                    "time": self.last_monitored
                },
                "data": {
                    "went_down_at": {
                        "current": self.last_monitored,
                        "previous": self.none
                    }
                },
                "message": "Error message",
                "code": 5004,
            }
        }

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
            'result']['data']['open_file_descriptors']['current'] = \
            self.percent_usage + 46
        self.data_received_initially_warning_alert[
            'result']['data']['system_cpu_usage']['current'] = \
            self.percent_usage + 46
        self.data_received_initially_warning_alert[
            'result']['data']['system_ram_usage']['current'] = \
            self.percent_usage + 46
        self.data_received_initially_warning_alert[
            'result']['data']['system_storage_usage']['current'] = \
            self.percent_usage + 46

        self.data_received_below_warning_threshold = \
            copy.deepcopy(self.data_received_initially_no_alert)

        self.data_received_below_warning_threshold[
            'result']['data']['open_file_descriptors']['previous'] = \
            self.percent_usage + 46
        self.data_received_below_warning_threshold[
            'result']['data']['system_cpu_usage']['previous'] = \
            self.percent_usage + 46
        self.data_received_below_warning_threshold[
            'result']['data']['system_ram_usage']['previous'] = \
            self.percent_usage + 46
        self.data_received_below_warning_threshold[
            'result']['data']['system_storage_usage']['previous'] = \
            self.percent_usage + 46

        self.data_received_initially_critical_alert = \
            copy.deepcopy(self.data_received_initially_no_alert)

        self.data_received_initially_critical_alert[
            'result']['data']['open_file_descriptors']['current'] = \
            self.percent_usage + 56
        self.data_received_initially_critical_alert[
            'result']['data']['system_cpu_usage']['current'] = \
            self.percent_usage + 56
        self.data_received_initially_critical_alert[
            'result']['data']['system_ram_usage']['current'] = \
            self.percent_usage + 56
        self.data_received_initially_critical_alert[
            'result']['data']['system_storage_usage']['current'] = \
            self.percent_usage + 56

        self.data_received_below_critical_above_warning = \
            copy.deepcopy(self.data_received_initially_warning_alert)

        self.data_received_below_critical_above_warning[
            'result']['data']['open_file_descriptors']['previous'] = \
            self.percent_usage + 56
        self.data_received_below_critical_above_warning[
            'result']['data']['system_cpu_usage']['previous'] = \
            self.percent_usage + 56
        self.data_received_below_critical_above_warning[
            'result']['data']['system_ram_usage']['previous'] = \
            self.percent_usage + 56
        self.data_received_below_critical_above_warning[
            'result']['data']['system_storage_usage']['previous'] = \
            self.percent_usage + 56

        # Alert used for rabbitMQ testing
        self.alert = OpenFileDescriptorsIncreasedAboveThresholdAlert(
            self.system_name, self.percent_usage + 46, self.warning,
            self.last_monitored, self.warning, self.parent_id,
            self.system_id
        )

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        try:
            self.test_manager.rabbitmq.connect_till_successful()
            self.test_manager.rabbitmq.queue_purge(self.test_queue_name)
            self.test_manager.rabbitmq.queue_purge(self.queue_used)
            self.test_manager.rabbitmq.queue_purge(self.target_queue_used)
            self.test_manager.rabbitmq.queue_delete(self.test_queue_name)
            self.test_manager.rabbitmq.queue_delete(self.queue_used)
            self.test_manager.rabbitmq.queue_delete(self.target_queue_used)
            self.test_manager.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
            self.test_manager.rabbitmq.exchange_delete(ALERT_EXCHANGE)
            self.test_manager.rabbitmq.disconnect()
        except Exception as e:
            print("Test failed: %s".format(e))

        self.dummy_logger = None
        self.rabbitmq = None
        self.publishing_queue = None
        self.test_system_alerter = None
        self.test_system_alerter_warnings_disabled = None
        self.test_system_alerter_critical_disabled = None
        self.test_system_alerter_all_disabled = None
        self.system_alerts_config = None
        self.system_alerts_config_warnings_disabled = None
        self.system_alerts_config_critical_disabled = None
        self.system_alerts_config_all_disabled = None

    def test_returns_alerter_name_as_str(self) -> None:
        self.assertEqual(self.alerter_name, self.test_system_alerter.__str__())

    def test_returns_alerter_name(self) -> None:
        self.assertEqual(self.alerter_name,
                         self.test_system_alerter.alerter_name)

    def test_returns_logger(self) -> None:
        self.assertEqual(self.dummy_logger, self.test_system_alerter.logger)

    def test_returns_publishing_queue_size(self) -> None:
        self.assertEqual(self.publishing_queue.qsize(),
                         self.test_system_alerter.publishing_queue.qsize())

    def test_returns_alerts_configs_from_alerter(self) -> None:
        self.assertEqual(self.system_alerts_config,
                         self.test_system_alerter.alerts_configs)

    """
    ###################### Tests without using RabbitMQ #######################
    """

    @mock.patch.object(SystemAlerter, "_classify_alert")
    def test_alerts_initial_run_no_alerts_count_classify_alert(
            self, mock_classify_alert) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            self.assertEqual(4, mock_classify_alert.call_count)
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    """
    ############## 1st run no increase/decrease alerts
    """

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert", autospec=True)
    def test_open_file_descriptors_initial_run_no_increase_alerts(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    """
    ########### 1st run increase/decrease alerts, 2nd run no increase/decrease alerts
    """

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert", autospec=True)
    def test_open_file_descriptors_initial_run_no_increase_alerts_then_no_increase_alerts(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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

    """
    ####### 1st run no alerts on increase/decrease, 2nd run warning alert on increase
    """

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert", autospec=True)
    def test_open_file_descriptors_initial_run_no_increase_alerts_then_warning_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['open_file_descriptors']['current'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['open_file_descriptors']['current'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_cpu_usage']['current'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_cpu_usage']['current'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_ram_usage']['current'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_ram_usage']['current'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_storage_usage']['current'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_storage_usage']['current'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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

    """
    1st run no increase/decrease alerts, 2nd run critical increase alerts
    """

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert", autospec=True)
    def test_open_file_descriptors_initial_run_no_increase_alerts_then_critical_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['open_file_descriptors']['current'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['open_file_descriptors']['current'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_cpu_usage']['current'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_cpu_usage']['current'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_ram_usage']['current'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_ram_usage']['current'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_storage_usage']['current'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_storage_usage']['current'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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

    """
    1st run warning alerts on increase
    """

    @mock.patch.object(SystemAlerter, "_classify_alert")
    def test_alerts_initial_run_warning_alerts_count_classify_alert(
            self, mock_classify_alert) -> None:
        data_for_alerting = []
        data = self.data_received_initially_warning_alert['result']['data']
        meta_data = self.data_received_initially_warning_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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

    """
    ########## 1st run warning alert on increase, 2nd run info alerts on decrease 
    """

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert", autospec=True)
    def test_open_file_descriptors_initial_run_warning_alert_then_no_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['open_file_descriptors']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['open_file_descriptors']['current'] = self.percent_usage + 36
        data['open_file_descriptors']['previous'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_cpu_usage']['current'] = self.percent_usage + 36
        data['system_cpu_usage']['previous'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_ram_usage']['current'] = self.percent_usage + 36
        data['system_ram_usage']['previous'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_storage_usage']['current'] = self.percent_usage + 36
        data['system_storage_usage']['previous'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
    @mock.patch("src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_all_alerts_above_warning_threshold_then_below_warning(
            self, mock_system_storage_usage_decrease,
            mock_system_ram_usage_decrease, mock_cpu_usage_decrease,
            mock_open_file_usage_decrease, mock_system_storage_usage_increase,
            mock_system_ram_usage_increase, mock_cpu_usage_increase,
            mock_open_file_usage_increase) -> None:
        data_for_alerting = []
        data = self.data_received_initially_warning_alert['result']['data']
        meta_data = self.data_received_initially_warning_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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

    """
    #### 1st run warning alerts on increase, 2nd run critical alerts on increase
    """

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert", autospec=True)
    def test_open_file_descriptors_initial_run_warning_alerts_then_critical_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['open_file_descriptors']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['open_file_descriptors']['current'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_cpu_usage']['current'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_ram_usage']['current'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_storage_usage']['current'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_all_alerts_above_warning_threshold_then_above_critical(
            self, mock_system_storage_usage_increase,
            mock_system_ram_usage_increase, mock_cpu_usage_increase,
            mock_open_file_usage_increase) -> None:
        data_for_alerting = []
        data = self.data_received_initially_warning_alert['result']['data']
        meta_data = self.data_received_initially_warning_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        data = self.data_received_initially_critical_alert['result']['data']
        meta_data = self.data_received_initially_critical_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_system_storage_usage_increase.assert_called_with(
                self.system_name, data['system_storage_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            mock_system_ram_usage_increase.assert_called_with(
                self.system_name, data['system_ram_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            mock_cpu_usage_increase.assert_called_with(
                self.system_name, data['system_cpu_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            mock_open_file_usage_increase.assert_called_with(
                self.system_name, data['open_file_descriptors']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(4, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    """
    ####### 1st run warning alert on increase, 2nd run no alert on increase in warning
    """

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert", autospec=True)
    def test_open_file_descriptors_initial_run_warning_alerts_then_increase_in_warning_no_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['open_file_descriptors']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['open_file_descriptors']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['open_file_descriptors']['current'] = self.percent_usage + 47
        data['open_file_descriptors']['previous'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['open_file_descriptors']['previous'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert", autospec=True)
    def test_open_file_descriptors_initial_run_no_decrease_alerts_on_warning_alert_then_no_decrease_alerts_on_warning_increase(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['open_file_descriptors']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['open_file_descriptors']['current'] = self.percent_usage + 47
        data['open_file_descriptors']['previous'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_cpu_usage_initial_run_warning_alert_then_no_alert_on_warning_increase(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_cpu_usage']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_cpu_usage']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_cpu_usage']['current'] = self.percent_usage + 47
        data['system_cpu_usage']['previous'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_with(
                self.system_name, data['system_cpu_usage']['previous'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_system_cpu_usage_initial_run_no_decrease_on_warning_then_no_decrease_alerts_on_warning_increase(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_cpu_usage']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_cpu_usage']['current'] = self.percent_usage + 47
        data['system_cpu_usage']['previous'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_ram_usage_initial_run_warning_alert_then_no_alert_in_warning(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_ram_usage']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_ram_usage']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_ram_usage']['current'] = self.percent_usage + 47
        data['system_ram_usage']['previous'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_with(
                self.system_name, data['system_ram_usage']['previous'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_system_ram_usage_initial_run_no_decrease_alerts_on_warning_then_no_decrease_alerts_on_warning_increase(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_ram_usage']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_ram_usage']['current'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_storage_usage_initial_run_warning_alert_then_no_alert_on_warning_increase(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_storage_usage']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_storage_usage']['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_storage_usage']['current'] = self.percent_usage + 47
        data['system_storage_usage']['previous'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_with(
                self.system_name, data['system_storage_usage']['previous'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_system_storage_usage_initial_run_no_decrease_alerts_on_warning_then_no_decrease_alerts_on_warning_increase(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_storage_usage']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_storage_usage']['current'] = self.percent_usage + 47
        data['system_storage_usage']['current'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    """
    ###### 1st run critical alerts on increase
    """

    @mock.patch.object(SystemAlerter, "_classify_alert")
    def test_alerts_initial_run_critical_alerts_count_classify_alert(
            self, mock_classify_alert) -> None:
        data_for_alerting = []
        data = self.data_received_initially_critical_alert['result']['data']
        meta_data = self.data_received_initially_critical_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            self.assertEqual(4, mock_classify_alert.call_count)
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert", autospec=True)
    def test_open_file_descriptors_initial_run_critical_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['open_file_descriptors']['current'] = self.percent_usage + 56
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
    def test_open_file_descriptors_initial_run_no_decrease_alerts_on_critical_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['open_file_descriptors']['current'] = self.percent_usage + 56
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_cpu_usage_initial_run_critical_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_cpu_usage']['current'] = self.percent_usage + 56
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
    def test_system_cpu_usage_initial_run_no_decrease_alerts_on_critical_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_cpu_usage']['current'] = self.percent_usage + 56
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_ram_usage_initial_run_critical_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_ram_usage']['current'] = self.percent_usage + 56
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
    def test_system_ram_usage_initial_run_no_decrease_alerts_on_critical_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_ram_usage']['current'] = self.percent_usage + 56
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_storage_usage_initial_run_critical_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_storage_usage']['current'] = self.percent_usage + 56
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
    def test_system_storage_usage_initial_run_no_decrease_alerts_on_critical_alert(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_storage_usage']['current'] = self.percent_usage + 56
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
    def test_alerts_initial_run_critical_alerts_count_alerts(
            self, mock_system_storage_usage_decrease,
            mock_system_ram_usage_decrease, mock_cpu_usage_decrease,
            mock_open_file_usage_decrease, mock_system_storage_usage_increase,
            mock_system_ram_usage_increase, mock_cpu_usage_increase,
            mock_open_file_usage_increase) -> None:
        data_for_alerting = []
        data = self.data_received_initially_critical_alert['result']['data']
        meta_data = self.data_received_initially_critical_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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

    """
    ######### 1st run above critical, second run between warning and critical
    """

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert", autospec=True)
    def test_open_file_descriptors_critical_alerts_then_no_increase_alerts_on_decrease_between_critical_and_warning(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['open_file_descriptors']['current'] = self.percent_usage + 56
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['open_file_descriptors']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['open_file_descriptors']['current'] = self.percent_usage + 50
        data['open_file_descriptors']['previous'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['open_file_descriptors']['previous'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert", autospec=True)
    def test_open_file_descriptors_critical_alerts_then_info_alerts_on_decrease_between_critical_warning(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['open_file_descriptors']['current'] = self.percent_usage + 56
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        self.test_system_alerter._create_state_for_system(self.system_id)
        data['open_file_descriptors']['current'] = self.percent_usage + 50
        data['open_file_descriptors']['previous'] = self.percent_usage + 56
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['open_file_descriptors']['current'],
                self.info, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_cpu_usage_critical_alerts_then_no_increase_alerts_on_decrease_between_critical_and_warning(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_cpu_usage']['current'] = self.percent_usage + 56
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_cpu_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_cpu_usage']['current'] = self.percent_usage + 50
        data['system_cpu_usage']['previous'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_cpu_usage']['previous'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_system_cpu_usage_critical_alerts_then_info_alerts_on_decrease_between_critical_warning(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_cpu_usage']['current'] = self.percent_usage + 56
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_cpu_usage']['current'] = self.percent_usage + 50
        data['system_cpu_usage']['previous'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_cpu_usage']['current'],
                self.info, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_ram_usage_critical_alerts_then_no_increase_alerts_on_decrease_between_critical_and_warning(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_ram_usage']['current'] = self.percent_usage + 56
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_ram_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_ram_usage']['current'] = self.percent_usage + 50
        data['system_ram_usage']['previous'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_ram_usage']['previous'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_system_ram_usage_critical_alerts_then_info_alerts_on_decrease_between_critical_warning(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_ram_usage']['current'] = self.percent_usage + 56
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_ram_usage']['current'] = self.percent_usage + 50
        data['system_ram_usage']['previous'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_ram_usage']['current'],
                self.info, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_storage_usage_critical_alerts_then_no_increase_alerts_on_decrease_between_critical_and_warning(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_storage_usage']['current'] = self.percent_usage + 56
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_storage_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_storage_usage']['current'] = self.percent_usage + 50
        data['system_storage_usage']['previous'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_storage_usage']['previous'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert", autospec=True)
    def test_system_storage_usage_critical_alerts_then_info_alerts_on_decrease_between_critical_warning(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_storage_usage']['current'] = self.percent_usage + 56
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_storage_usage']['current'] = self.percent_usage + 50
        data['system_storage_usage']['previous'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_storage_usage']['current'],
                self.info, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
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

    """
    1st run above critical, 2nd run above critical but repeat timer hasn't elapsed so no alerts
    """

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.TimedTaskLimiter.last_time_that_did_task", autospec=True)
    def test_open_file_descriptors_critical_alerts_then_no_alerts_on_increase_before_repeat_timer_elapsed(
            self, mock_last_time_that_did_task, mock_percentage_usage) -> None:
        mock_last_time_that_did_task.return_value = self.last_monitored
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['open_file_descriptors']['current'] = self.percent_usage + 56
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['open_file_descriptors']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['open_file_descriptors']['current'] = self.percent_usage + 58
        data['open_file_descriptors']['previous'] = self.percent_usage + 56
        meta_data['last_monitored'] = self.last_monitored + self.critical_repeat_seconds - 1
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['open_file_descriptors']['previous'],
                self.critical, self.last_monitored, self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.TimedTaskLimiter.last_time_that_did_task", autospec=True)
    def test_system_cpu_usage_critical_alerts_then_no_alerts_on_increase_before_repeat_timer_elapsed(
            self, mock_last_time_that_did_task, mock_percentage_usage) -> None:
        mock_last_time_that_did_task.return_value = self.last_monitored
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_cpu_usage']['current'] = self.percent_usage + 56
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_cpu_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_cpu_usage']['current'] = self.percent_usage + 58
        data['system_cpu_usage']['previous'] = self.percent_usage + 56
        meta_data['last_monitored'] = self.last_monitored + self.critical_repeat_seconds - 1
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_cpu_usage']['previous'],
                self.critical, self.last_monitored, self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.TimedTaskLimiter.last_time_that_did_task", autospec=True)
    def test_system_ram_usage_critical_alerts_then_no_alerts_on_increase_before_repeat_timer_elapsed(
            self, mock_last_time_that_did_task, mock_percentage_usage) -> None:
        mock_last_time_that_did_task.return_value = self.last_monitored
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_ram_usage']['current'] = self.percent_usage + 56
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_ram_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_ram_usage']['current'] = self.percent_usage + 58
        data['system_ram_usage']['previous'] = self.percent_usage + 56
        meta_data['last_monitored'] = self.last_monitored + self.critical_repeat_seconds - 1
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_ram_usage']['previous'],
                self.critical, self.last_monitored, self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.TimedTaskLimiter.last_time_that_did_task", autospec=True)
    def test_system_storage_usage_critical_alerts_then_no_alerts_on_increase_before_repeat_timer_elapsed(
            self, mock_last_time_that_did_task, mock_percentage_usage) -> None:
        mock_last_time_that_did_task.return_value = self.last_monitored
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_storage_usage']['current'] = self.percent_usage + 56
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_storage_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['system_storage_usage']['current'] = self.percent_usage + 58
        data['system_storage_usage']['previous'] = self.percent_usage + 56
        meta_data['last_monitored'] = self.last_monitored + self.critical_repeat_seconds - 1
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_storage_usage']['previous'],
                self.critical, self.last_monitored, self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    """
    1st run above critical, 2nd run above critical and repeat timer has elapsed so a critical alert is sent
    """

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.TimedTaskLimiter.last_time_that_did_task", autospec=True)
    def test_open_file_descriptors_critical_alerts_then_critical_alert_on_same_value_after_repeat_timer_elapsed(
            self, mock_last_time_that_did_task, mock_percentage_usage) -> None:

        mock_last_time_that_did_task.return_value = self.last_monitored
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['open_file_descriptors']['current'] = self.percent_usage + 56
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['open_file_descriptors']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        meta_data['last_monitored'] = self.last_monitored + self.critical_repeat_seconds
        data['open_file_descriptors']['current'] = self.percent_usage + 56
        data['open_file_descriptors']['previous'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_with(
                self.system_name, data['open_file_descriptors']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.TimedTaskLimiter.last_time_that_did_task", autospec=True)
    def test_system_cpu_usage_critical_alerts_then_critical_alert_on_same_value_after_repeat_timer_elapsed(
            self, mock_last_time_that_did_task, mock_percentage_usage) -> None:

        mock_last_time_that_did_task.return_value = self.last_monitored
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_cpu_usage']['current'] = self.percent_usage + 56
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_cpu_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        meta_data['last_monitored'] = self.last_monitored + self.critical_repeat_seconds
        data['system_cpu_usage']['current'] = self.percent_usage + 56
        data['system_cpu_usage']['previous'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_with(
                self.system_name, data['system_cpu_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.TimedTaskLimiter.last_time_that_did_task", autospec=True)
    def test_system_ram_usage_critical_alerts_then_critical_alert_on_same_value_after_repeat_timer_elapsed(
            self, mock_last_time_that_did_task, mock_percentage_usage) -> None:

        mock_last_time_that_did_task.return_value = self.last_monitored
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_ram_usage']['current'] = self.percent_usage + 56
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_ram_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        meta_data['last_monitored'] = self.last_monitored + self.critical_repeat_seconds
        data['system_ram_usage']['current'] = self.percent_usage + 56
        data['system_ram_usage']['previous'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_with(
                self.system_name, data['system_ram_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.TimedTaskLimiter.last_time_that_did_task", autospec=True)
    def test_system_storage_usage_critical_alerts_then_critical_alert_on_same_value_after_repeat_timer_elapsed(
            self, mock_last_time_that_did_task, mock_percentage_usage) -> None:

        mock_last_time_that_did_task.return_value = self.last_monitored
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_storage_usage']['current'] = self.percent_usage + 56
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_storage_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        meta_data['last_monitored'] = self.last_monitored + self.critical_repeat_seconds
        data['system_storage_usage']['current'] = self.percent_usage + 56
        data['system_storage_usage']['previous'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_with(
                self.system_name, data['system_storage_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    """
    1st run above critical, 2nd run above critical but below previous and
    repeat timer has elapsed so a critical alert is sent
    """

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.TimedTaskLimiter.last_time_that_did_task", autospec=True)
    def test_open_file_descriptors_critical_alerts_then_critical_alert_on_lower_value_after_repeat_timer_elapsed(
            self, mock_last_time_that_did_task, mock_percentage_usage) -> None:

        mock_last_time_that_did_task.return_value = self.last_monitored
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['open_file_descriptors']['current'] = self.percent_usage + 57
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['open_file_descriptors']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        meta_data['last_monitored'] = self.last_monitored + self.critical_repeat_seconds
        data['open_file_descriptors']['current'] = self.percent_usage + 56
        data['open_file_descriptors']['previous'] = self.percent_usage + 57
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_with(
                self.system_name, data['open_file_descriptors']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.TimedTaskLimiter.last_time_that_did_task", autospec=True)
    def test_system_cpu_usage_critical_alerts_then_critical_alert_on_lower_value_after_repeat_timer_elapsed(
            self, mock_last_time_that_did_task, mock_percentage_usage) -> None:

        mock_last_time_that_did_task.return_value = self.last_monitored
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_cpu_usage']['current'] = self.percent_usage + 57
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_cpu_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        meta_data['last_monitored'] = self.last_monitored + self.critical_repeat_seconds
        data['system_cpu_usage']['current'] = self.percent_usage + 56
        data['system_cpu_usage']['previous'] = self.percent_usage + 57
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_with(
                self.system_name, data['system_cpu_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.TimedTaskLimiter.last_time_that_did_task", autospec=True)
    def test_system_ram_usage_critical_alerts_then_critical_alert_on_lower_value_after_repeat_timer_elapsed(
            self, mock_last_time_that_did_task, mock_percentage_usage) -> None:

        mock_last_time_that_did_task.return_value = self.last_monitored
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_ram_usage']['current'] = self.percent_usage + 57
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_ram_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        meta_data['last_monitored'] = self.last_monitored + self.critical_repeat_seconds
        data['system_ram_usage']['current'] = self.percent_usage + 56
        data['system_ram_usage']['previous'] = self.percent_usage + 57
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_with(
                self.system_name, data['system_ram_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.TimedTaskLimiter.last_time_that_did_task", autospec=True)
    def test_system_storage_usage_critical_alerts_then_critical_alert_on_lower_value_after_repeat_timer_elapsed(
            self, mock_last_time_that_did_task, mock_percentage_usage) -> None:

        mock_last_time_that_did_task.return_value = self.last_monitored
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_storage_usage']['current'] = self.percent_usage + 57
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_once_with(
                self.system_name, data['system_storage_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        meta_data['last_monitored'] = self.last_monitored + self.critical_repeat_seconds
        data['system_storage_usage']['current'] = self.percent_usage + 56
        data['system_storage_usage']['previous'] = self.percent_usage + 57
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_called_with(
                self.system_name, data['system_storage_usage']['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    """
    Testing System back up alerts 
    """

    @mock.patch("src.alerter.alerters.system.SystemBackUpAgainAlert", autospec=True)
    def test_system_back_up_no_alert(self, mock_system_back_up) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_system_back_up.assert_not_called()
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemBackUpAgainAlert", autospec=True)
    def test_system_back_up_alert(self, mock_system_back_up) -> None:
        data_for_alerting = []
        self.test_system_alerter._system_initial_downtime_alert_sent[self.system_id] = True
        data = self.data_received_initially_no_alert['result']['data']
        data['went_down_at']['previous'] = self.last_monitored
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_system_back_up.assert_called_once_with(
                self.system_name, self.info, self.last_monitored,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.TimedTaskLimiter.reset", autospec=True)
    def test_system_back_up_timed_task_limiter_reset(self, mock_reset) -> None:
        data_for_alerting = []
        # Set that the initial downtime alert was sent already
        self.test_system_alerter._system_initial_downtime_alert_sent[self.system_id] = True
        data = self.data_received_initially_no_alert['result']['data']
        data['went_down_at']['previous'] = self.last_monitored
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_reset.assert_called_once()
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    """
    Testing System went down at alerts
    """

    @mock.patch("src.alerter.alerters.system.SystemWentDownAtAlert", autospec=True)
    def test_system_went_down_at_no_alert_below_warning_threshold(self, mock_system_is_down) -> None:
        data_for_alerting = []
        data = self.data_received_error_data['error']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_errors(
            data, data_for_alerting)
        try:
            mock_system_is_down.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    """
    These tests assume that critical_threshold_seconds > warning_threshold_seconds
    """

    @mock.patch("src.alerter.alerters.system.SystemWentDownAtAlert", autospec=True)
    def test_system_went_down_at_alert_above_warning_threshold(
            self, mock_system_is_down) -> None:
        data_for_alerting = []
        data = self.data_received_error_data['error']
        data['meta_data']['time'] = self.last_monitored + self.warning_threshold_seconds
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_errors(
            data, data_for_alerting)
        try:
            mock_system_is_down.assert_called_once_with(
                self.system_name, self.warning, data['meta_data']['time'],
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemWentDownAtAlert", autospec=True)
    def test_system_went_down_at_alert_above_critical_threshold(
            self, mock_system_is_down) -> None:
        data_for_alerting = []
        data = self.data_received_error_data['error']
        data['meta_data']['time'] = self.last_monitored + self.critical_threshold_seconds
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_errors(
            data, data_for_alerting)
        try:
            mock_system_is_down.assert_called_once_with(
                self.system_name, self.critical, data['meta_data']['time'],
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStillDownAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemWentDownAtAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.TimedTaskLimiter.last_time_that_did_task", autospec=True)
    def test_system_went_down_at_alert_above_warning_threshold_then_no_critical_repeat(
            self, mock_last_time_did_task, mock_system_is_down,
            mock_system_still_down) -> None:
        data_for_alerting = []
        data = self.data_received_error_data['error']
        past_warning_time = self.last_monitored + self.warning_threshold_seconds
        mock_last_time_did_task.return_value = past_warning_time
        data['meta_data']['time'] = past_warning_time
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_errors(
            data, data_for_alerting)
        try:
            mock_system_is_down.assert_called_once_with(
                self.system_name, self.warning, past_warning_time,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['meta_data']['time'] = past_warning_time + self.critical_repeat_seconds - 1
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_errors(
            data, data_for_alerting)
        try:
            mock_system_is_down.assert_called_once_with(
                self.system_name, self.warning, past_warning_time,
                self.parent_id, self.system_id
            )
            mock_system_still_down.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStillDownAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemWentDownAtAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.TimedTaskLimiter.last_time_that_did_task", autospec=True)
    def test_system_went_down_at_alert_above_warning_threshold_then_critical_repeat(
            self, mock_last_time_did_task, mock_system_is_down, mock_system_still_down) -> None:
        data_for_alerting = []
        data = self.data_received_error_data['error']
        past_warning_time = self.last_monitored + self.warning_threshold_seconds
        mock_last_time_did_task.return_value = past_warning_time
        data['meta_data']['time'] = past_warning_time
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_errors(
            data, data_for_alerting)
        try:
            mock_system_is_down.assert_called_once_with(
                self.system_name, self.warning, past_warning_time,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['meta_data']['time'] = past_warning_time + self.critical_repeat_seconds
        downtime = int(data['meta_data']['time'] - self.last_monitored)
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_errors(
            data, data_for_alerting)
        try:
            mock_system_is_down.assert_called_once_with(
                self.system_name, self.warning, past_warning_time,
                self.parent_id, self.system_id
            )
            mock_system_still_down.assert_called_once_with(
                self.system_name, downtime, self.critical,
                data['meta_data']['time'], self.parent_id,
                self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStillDownAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemWentDownAtAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.TimedTaskLimiter.last_time_that_did_task", autospec=True)
    def test_system_went_down_at_alert_above_critical_threshold_then_no_critical_repeat(
            self, mock_last_time_did_task, mock_system_is_down,
            mock_system_still_down) -> None:
        data_for_alerting = []
        data = self.data_received_error_data['error']
        past_critical_time = self.last_monitored + self.critical_threshold_seconds
        mock_last_time_did_task.return_value = past_critical_time
        data['meta_data']['time'] = past_critical_time
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_errors(
            data, data_for_alerting)
        try:
            mock_system_is_down.assert_called_once_with(
                self.system_name, self.critical, past_critical_time,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['meta_data']['time'] = past_critical_time + self.critical_repeat_seconds - 1
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_errors(
            data, data_for_alerting)
        try:
            mock_system_is_down.assert_called_once_with(
                self.system_name, self.critical, past_critical_time,
                self.parent_id, self.system_id
            )
            mock_system_still_down.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStillDownAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemWentDownAtAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.TimedTaskLimiter.last_time_that_did_task", autospec=True)
    def test_system_went_down_at_alert_above_warning_threshold_then_critical_repeat(
            self, mock_last_time_did_task, mock_system_is_down, mock_system_still_down) -> None:
        data_for_alerting = []
        data = self.data_received_error_data['error']
        past_critical_time = self.last_monitored + self.critical_threshold_seconds
        mock_last_time_did_task.return_value = past_critical_time
        data['meta_data']['time'] = past_critical_time
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_errors(
            data, data_for_alerting)
        try:
            mock_system_is_down.assert_called_once_with(
                self.system_name, self.critical, past_critical_time,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['meta_data']['time'] = past_critical_time + self.critical_repeat_seconds
        downtime = int(data['meta_data']['time'] - self.last_monitored)
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_errors(
            data, data_for_alerting)
        try:
            mock_system_is_down.assert_called_once_with(
                self.system_name, self.critical, past_critical_time,
                self.parent_id, self.system_id
            )
            mock_system_still_down.assert_called_once_with(
                self.system_name, downtime, self.critical,
                data['meta_data']['time'], self.parent_id,
                self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    """
    Testing error alerts of MetricNotFound and InvalidURL
    """

    @mock.patch("src.alerter.alerters.system.MetricNotFoundErrorAlert", autospec=True)
    def test_metric_not_found_alert(self, mock_alert) -> None:
        data_for_alerting = []
        data = self.data_received_error_data['error']
        data['code'] = 5003
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_errors(
            data, data_for_alerting)
        try:
            mock_alert.assert_called_once_with(
                self.system_name, data['message'], self.error,
                data['meta_data']['time'], self.parent_id,
                self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.InvalidUrlAlert", autospec=True)
    def test_invalid_url_alert(self, mock_alert) -> None:
        data_for_alerting = []
        data = self.data_received_error_data['error']
        data['code'] = 5009
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_errors(
            data, data_for_alerting)
        try:
            mock_alert.assert_called_once_with(
                self.system_name, data['message'], self.error,
                data['meta_data']['time'], self.parent_id,
                self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    """
    1st run above warning threshold no alerts as warning alerts are disabled
    """

    @mock.patch.object(SystemAlerter, "_classify_alert")
    def test_alerts_warning_alerts_disabled_metric_above_warning_threshold(
            self, mock_classify_alert) -> None:
        data_for_alerting = []
        data = self.data_received_initially_warning_alert['result']['data']
        meta_data = self.data_received_initially_warning_alert['result']['meta_data']
        self.test_system_alerter_warnings_disabled._create_state_for_system(self.system_id)
        self.test_system_alerter_warnings_disabled._process_results(
            data, meta_data, data_for_alerting)
        try:
            self.assertEqual(4, mock_classify_alert.call_count)
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert", autospec=True)
    def test_open_file_descriptors_warning_alerts_disabled_increase_above_warning_threshold(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['open_file_descriptors']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter_warnings_disabled._create_state_for_system(self.system_id)
        self.test_system_alerter_warnings_disabled._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_cpu_usage_warning_alerts_disabled_increase_above_warning_threshold(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_cpu_usage']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter_warnings_disabled._create_state_for_system(self.system_id)
        self.test_system_alerter_warnings_disabled._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_ram_usage_warning_alerts_disabled_increase_above_warning_threshold(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_ram_usage']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter_warnings_disabled._create_state_for_system(self.system_id)
        self.test_system_alerter_warnings_disabled._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_storage_usage_warning_alerts_disabled_increase_above_warning_threshold(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_storage_usage']['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter_warnings_disabled._create_state_for_system(self.system_id)
        self.test_system_alerter_warnings_disabled._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    """
    1st run above critical threshold no alerts as critical alerts are disabled
    """

    @mock.patch.object(SystemAlerter, "_classify_alert")
    def test_alerts_critical_alerts_disabled_metric_above_critical_threshold(
            self, mock_classify_alert) -> None:
        data_for_alerting = []
        data = self.data_received_initially_warning_alert['result']['data']
        meta_data = self.data_received_initially_warning_alert['result']['meta_data']
        self.test_system_alerter_critical_disabled._create_state_for_system(self.system_id)
        self.test_system_alerter_critical_disabled._process_results(
            data, meta_data, data_for_alerting)
        try:
            self.assertEqual(4, mock_classify_alert.call_count)
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert", autospec=True)
    def test_open_file_descriptors_critical_alerts_disabled_increase_above_critical_threshold(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['open_file_descriptors']['current'] = self.percent_usage + 56
        data['open_file_descriptors']['previous'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter_critical_disabled._create_state_for_system(self.system_id)
        self.test_system_alerter_critical_disabled._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_cpu_usage_critical_alerts_disabled_increase_above_critical_threshold(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_cpu_usage']['current'] = self.percent_usage + 56
        data['system_cpu_usage']['previous'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter_critical_disabled._create_state_for_system(self.system_id)
        self.test_system_alerter_critical_disabled._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_ram_usage_critical_alerts_disabled_increase_above_critical_threshold(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_ram_usage']['current'] = self.percent_usage + 56
        data['system_ram_usage']['previous'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter_critical_disabled._create_state_for_system(self.system_id)
        self.test_system_alerter_critical_disabled._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert", autospec=True)
    def test_system_storage_usage_critical_alerts_disabled_increase_above_critical_threshold(
            self, mock_percentage_usage) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data['system_storage_usage']['current'] = self.percent_usage + 56
        data['system_storage_usage']['previous'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter_critical_disabled._create_state_for_system(self.system_id)
        self.test_system_alerter_critical_disabled._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_percentage_usage.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    """
    1st above critical all alerts disabled
    """

    @mock.patch.object(SystemAlerter, "_classify_alert")
    def test_alerts_all_alerts_disabled_metric_above_critical_threshold_and_warning_threshold(
            self, mock_classify_alert) -> None:
        data_for_alerting = []
        data = self.data_received_initially_critical_alert['result']['data']
        meta_data = self.data_received_initially_critical_alert['result']['meta_data']
        self.test_system_alerter_all_disabled._create_state_for_system(self.system_id)
        self.test_system_alerter_all_disabled._process_results(
            data, meta_data, data_for_alerting)
        try:
            self.assertEqual(0, mock_classify_alert.call_count)
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    """
    ###################### Tests using RabbitMQ #######################
    """

    def test_initialise_rabbit_initialises_queues(self) -> None:
        self.test_system_alerter._initialise_rabbitmq()
        try:
            self.rabbitmq.connect_till_successful()
            self.rabbitmq.queue_declare(self.queue_used, passive=True)
        except pika.exceptions.ConnectionClosedByBroker:
            self.fail("Queue {} was not declared".format(self.queue_used))

    def test_initialise_rabbit_initialises_exchanges(self) -> None:
        self.test_system_alerter._initialise_rabbitmq()

        try:
            self.rabbitmq.connect_till_successful()
            self.rabbitmq.exchange_declare(ALERT_EXCHANGE, passive=True)
        except pika.exceptions.ConnectionClosedByBroker:
            self.fail("Exchange {} was not declared".format(ALERT_EXCHANGE))

    def test_send_warning_alerts_correctly(
            self) -> None:
        try:
            self.test_system_alerter._initialise_rabbitmq()
            self.test_system_alerter.rabbitmq.queue_delete(self.target_queue_used)

            res = self.test_system_alerter.rabbitmq.queue_declare(
                queue=self.target_queue_used, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_system_alerter.rabbitmq.queue_bind(
                queue=self.target_queue_used, exchange=ALERT_EXCHANGE,
                routing_key=self.alert_router_routing_key)

            self.test_system_alerter.rabbitmq.basic_publish_confirm(
                exchange=ALERT_EXCHANGE, routing_key=self.alert_router_routing_key,
                body=self.alert.alert_data, is_body_dict=True,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=True)

            res = self.test_system_alerter.rabbitmq.queue_declare(
                queue=self.target_queue_used, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            self.assertEqual(1, res.method.message_count)

            _, _, body = self.test_system_alerter.rabbitmq.basic_get(
                self.target_queue_used)
            # For some reason during the conversion [] are swapped to ()
            self.assertEqual(json.loads(json.dumps(self.alert.alert_data)), json.loads(body))

            self.test_system_alerter.rabbitmq.queue_purge(self.target_queue_used)
            self.test_system_alerter.rabbitmq.queue_delete(self.target_queue_used)
            self.test_system_alerter.rabbitmq.exchange_delete(ALERT_EXCHANGE)
            self.test_system_alerter.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    # Same test that is in monitors tests
    def test_send_heartbeat_sends_a_heartbeat_correctly(self) -> None:
        try:
            self.test_system_alerter._initialise_rabbitmq()
            self.test_system_alerter.rabbitmq.queue_delete(self.heartbeat_queue)

            res = self.test_system_alerter.rabbitmq.queue_declare(
                queue=self.heartbeat_queue, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_system_alerter.rabbitmq.queue_bind(
                queue=self.heartbeat_queue, exchange=HEALTH_CHECK_EXCHANGE,
                routing_key='heartbeat.worker')
            self.test_system_alerter._send_heartbeat(self.heartbeat_test)

            res = self.test_system_alerter.rabbitmq.queue_declare(
                queue=self.heartbeat_queue, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            self.assertEqual(1, res.method.message_count)

            _, _, body = self.test_system_alerter.rabbitmq.basic_get(
                self.heartbeat_queue)
            self.assertEqual(self.heartbeat_test, json.loads(body))

            self.test_system_alerter.rabbitmq.queue_purge(self.heartbeat_queue)
            self.test_system_alerter.rabbitmq.queue_delete(self.heartbeat_queue)
            self.test_system_alerter.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
            self.test_system_alerter.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    """
    Testing _process_data using RabbitMQ
    """

    @mock.patch("src.alerter.alerters.system.SystemAlerter._process_results")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._create_state_for_system")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_result_data_no_alerts(
            self, mock_ack, mock_create_state_for_system,
            mock_process_results) -> None:

        mock_ack.return_value = None

        try:
            self.test_system_alerter.rabbitmq.connect()
            blocking_channel = self.test_system_alerter.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.routing_key)
            body = json.dumps(self.data_received_initially_no_alert).encode()
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_create_state_for_system.assert_called_with(
                self.system_id
            )
            mock_process_results.assert_called_with(
                self.data_received_initially_no_alert['result']['data'],
                self.data_received_initially_no_alert['result']['meta_data'],
                []
            )
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemAlerter._process_errors")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._create_state_for_system")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_error_data_no_alerts(
            self, mock_ack, mock_create_state_for_system,
            mock_process_errors) -> None:

        mock_ack.return_value = None

        try:
            self.test_system_alerter.rabbitmq.connect()
            blocking_channel = self.test_system_alerter.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.routing_key)
            body = json.dumps(self.data_received_error_data).encode()
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_create_state_for_system.assert_called_with(
                self.system_id
            )
            mock_process_errors.assert_called_with(
                self.data_received_error_data['error'],
                []
            )
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._send_heartbeat")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._process_results")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._create_state_for_system")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_result_data_send_hb_no_proc_error(
            self, mock_ack, mock_create_state_for_system,
            mock_process_results, mock_send_heartbeat) -> None:

        mock_ack.return_value = None
        mock_create_state_for_system.return_value = None
        mock_process_results.return_value = None

        try:
            self.test_system_alerter.rabbitmq.connect()
            blocking_channel = self.test_system_alerter.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.routing_key)
            body = json.dumps(self.data_received_initially_no_alert).encode()
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_send_heartbeat.assert_called_with(self.heartbeat_test)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._send_heartbeat")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._process_errors")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._create_state_for_system")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_error_data_send_hb_no_proc_error(
            self, mock_ack, mock_create_state_for_system,
            mock_process_errors, mock_send_heartbeat) -> None:

        mock_ack.return_value = None
        mock_create_state_for_system.return_value = None
        mock_process_errors.return_value = None

        try:
            self.test_system_alerter.rabbitmq.connect()
            blocking_channel = self.test_system_alerter.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.routing_key)
            body = json.dumps(self.data_received_error_data).encode()
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_send_heartbeat.assert_called_with(self.heartbeat_test)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._send_heartbeat")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._process_results")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._create_state_for_system")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_result_data_do_not_send_hb_on_proc_error_bad_routing_key(
            self, mock_ack, mock_create_state_for_system,
            mock_process_results, mock_send_heartbeat) -> None:

        mock_ack.return_value = None
        mock_create_state_for_system.return_value = None
        mock_process_results.return_value = None

        try:
            self.test_system_alerter.rabbitmq.connect()
            blocking_channel = self.test_system_alerter.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.bad_routing_key)
            body = json.dumps(self.data_received_initially_no_alert).encode()
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_send_heartbeat.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._send_heartbeat")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._process_errors")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._create_state_for_system")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_error_data_do_not_send_hb_on_proc_error_bad_routing_key(
            self, mock_ack, mock_create_state_for_system,
            mock_process_errors, mock_send_heartbeat) -> None:

        mock_ack.return_value = None
        mock_create_state_for_system.return_value = None
        mock_process_errors.return_value = None

        try:
            self.test_system_alerter.rabbitmq.connect()
            blocking_channel = self.test_system_alerter.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.bad_routing_key)
            body = json.dumps(self.data_received_error_data).encode()
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_send_heartbeat.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemAlerter._send_data")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._process_results")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._create_state_for_system")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_result_data_send_data_called(
            self, mock_ack, mock_create_state_for_system,
            mock_process_results, mock_send_data) -> None:

        mock_ack.return_value = None
        mock_create_state_for_system.return_value = None
        mock_process_results.return_value = None

        try:
            self.test_system_alerter.rabbitmq.connect()
            blocking_channel = self.test_system_alerter.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.routing_key)
            body = json.dumps(self.data_received_initially_no_alert).encode()
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_send_data.assert_called_once()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemAlerter._send_data")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._process_errors")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._create_state_for_system")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_error_data_send_data_called(
            self, mock_ack, mock_create_state_for_system,
            mock_process_errors, mock_send_data) -> None:

        mock_ack.return_value = None
        mock_create_state_for_system.return_value = None
        mock_process_errors.return_value = None

        try:
            self.test_system_alerter.rabbitmq.connect()
            blocking_channel = self.test_system_alerter.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.routing_key)
            body = json.dumps(self.data_received_error_data).encode()
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_send_data.assert_called_once()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemAlerter._process_results")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._create_state_for_system")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_result_data_not_processed_bad_routing_key(
            self, mock_ack, mock_create_state_for_system,
            mock_process_results) -> None:
        mock_ack.return_value = None
        try:
            self.test_system_alerter.rabbitmq.connect()
            blocking_channel = self.test_system_alerter.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.bad_routing_key)
            body = json.dumps(self.data_received_initially_no_alert).encode()
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_create_state_for_system.assert_not_called()
            mock_process_results.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemAlerter._process_errors")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._create_state_for_system")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_error_data_not_processed_bad_routing_key(
            self, mock_ack, mock_create_state_for_system,
            mock_process_errors) -> None:

        mock_ack.return_value = None

        try:
            self.test_system_alerter.rabbitmq.connect()
            blocking_channel = self.test_system_alerter.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.bad_routing_key)
            body = json.dumps(self.data_received_error_data).encode()
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_create_state_for_system.assert_not_called()
            mock_process_errors.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemAlerter._process_results")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._create_state_for_system")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_result_data_not_processed_bad_data_received(
            self, mock_ack, mock_create_state_for_system,
            mock_process_results) -> None:
        mock_ack.return_value = None
        try:
            self.test_system_alerter.rabbitmq.connect()
            blocking_channel = self.test_system_alerter.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.bad_routing_key)
            del self.data_received_initially_no_alert['result']['data']
            body = json.dumps(self.data_received_initially_no_alert).encode()
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_create_state_for_system.assert_not_called()
            mock_process_results.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemAlerter._process_errors")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._create_state_for_system")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_error_data_not_processed_bad_data_received(
            self, mock_ack, mock_create_state_for_system,
            mock_process_errors) -> None:

        mock_ack.return_value = None

        try:
            self.test_system_alerter.rabbitmq.connect()
            blocking_channel = self.test_system_alerter.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.bad_routing_key)
            del self.data_received_error_data['error']['meta_data']
            body = json.dumps(self.data_received_error_data).encode()
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_create_state_for_system.assert_not_called()
            mock_process_errors.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemAlerter._place_latest_data_on_queue")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._process_results")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._create_state_for_system")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_result_data_send_data_called(
            self, mock_ack, mock_create_state_for_system,
            mock_process_results, mock_place_latest_data_on_queue) -> None:

        mock_ack.return_value = None
        mock_create_state_for_system.return_value = None
        mock_process_results.return_value = None

        try:
            self.test_system_alerter.rabbitmq.connect()
            blocking_channel = self.test_system_alerter.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.routing_key)
            body = json.dumps(self.data_received_initially_no_alert).encode()
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_place_latest_data_on_queue.assert_called_once()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemAlerter._place_latest_data_on_queue")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._process_errors")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._create_state_for_system")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_error_data_send_data_called(
            self, mock_ack, mock_create_state_for_system,
            mock_process_errors, mock_place_latest_data_on_queue) -> None:

        mock_ack.return_value = None
        mock_create_state_for_system.return_value = None
        mock_process_errors.return_value = None

        try:
            self.test_system_alerter.rabbitmq.connect()
            blocking_channel = self.test_system_alerter.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.routing_key)
            body = json.dumps(self.data_received_error_data).encode()
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_place_latest_data_on_queue.assert_called_once()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemAlerter._place_latest_data_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_place_latest_data_on_queue_not_called_bad_routing_key(
            self, mock_ack, mock_place_latest_data_on_queue) -> None:
        mock_ack.return_value = None
        try:
            self.test_system_alerter.rabbitmq.connect()
            blocking_channel = self.test_system_alerter.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.bad_routing_key)
            body = json.dumps(self.data_received_initially_no_alert).encode()
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_place_latest_data_on_queue.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))
    
    @mock.patch("src.alerter.alerters.system.SystemAlerter._place_latest_data_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_error_data_not_processed_bad_routing_key(
            self, mock_ack, mock_place_latest_data_on_queue) -> None:

        mock_ack.return_value = None
        try:
            self.test_system_alerter.rabbitmq.connect()
            blocking_channel = self.test_system_alerter.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.bad_routing_key)
            body = json.dumps(self.data_received_error_data).encode()
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_place_latest_data_on_queue.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemAlerter._place_latest_data_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_place_latest_data_on_queue_not_called_bad_data_received(
            self, mock_ack, mock_place_latest_data_on_queue) -> None:
        mock_ack.return_value = None
        try:
            self.test_system_alerter.rabbitmq.connect()
            blocking_channel = self.test_system_alerter.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.bad_routing_key)
            del self.data_received_initially_no_alert['result']['data']
            body = json.dumps(self.data_received_initially_no_alert).encode()
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_place_latest_data_on_queue.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemAlerter._place_latest_data_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_error_data_not_processed_bad_data_received(
            self, mock_ack, mock_place_latest_data_on_queue) -> None:
        mock_ack.return_value = None
        try:
            self.test_system_alerter.rabbitmq.connect()
            blocking_channel = self.test_system_alerter.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.bad_routing_key)
            del self.data_received_error_data['error']['meta_data']
            body = json.dumps(self.data_received_error_data).encode()
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_place_latest_data_on_queue.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))