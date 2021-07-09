import copy
import datetime
import json
import logging
import unittest
from queue import Queue
from unittest import mock

import pika
import pika.exceptions
from freezegun import freeze_time
from parameterized import parameterized

from src.alerter.alerters.system import SystemAlerter
from src.alerter.alerts.system_alerts import (
    OpenFileDescriptorsIncreasedAboveThresholdAlert)
from src.alerter.grouped_alerts_metric_code import GroupedSystemAlertsMetricCode
from src.configs.alerts.system import SystemAlertsConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.rabbitmq import (
    ALERT_EXCHANGE, HEALTH_CHECK_EXCHANGE,
    SYS_ALERTER_INPUT_QUEUE_NAME_TEMPLATE, SYSTEM_ALERT_ROUTING_KEY,
    SYSTEM_TRANSFORMED_DATA_ROUTING_KEY_TEMPLATE,
    HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY, TOPIC)
from src.utils.env import ALERTER_PUBLISHING_QUEUE_SIZE, RABBIT_IP


class TestSystemAlerter(unittest.TestCase):
    def setUp(self) -> None:
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.rabbit_ip = RABBIT_IP
        self.alert_input_exchange = ALERT_EXCHANGE
        self.connection_check_time_interval = datetime.timedelta(seconds=0)

        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)

        self.test_rabbit_manager = RabbitMQApi(
            self.dummy_logger, RABBIT_IP,
            connection_check_time_interval=self.connection_check_time_interval)

        self.alerter_name = 'test_alerter'
        self.system_id = 'test_system_id'
        self.parent_id = 'test_parent_id'
        self.system_name = 'test_system'
        self.last_monitored = 1611619200
        self.publishing_queue = Queue(ALERTER_PUBLISHING_QUEUE_SIZE)
        self.test_output_routing_key = 'test_alert.system'
        self.queue_used = SYS_ALERTER_INPUT_QUEUE_NAME_TEMPLATE.format(
            self.parent_id)
        self.target_queue_used = "alert_router_queue"
        self.input_routing_key = \
            SYSTEM_TRANSFORMED_DATA_ROUTING_KEY_TEMPLATE.format(self.parent_id)
        self.bad_output_routing_key = "alert.system.not_real"
        self.output_routing_key = SYSTEM_ALERT_ROUTING_KEY.format(
            self.parent_id)
        self.heartbeat_queue = 'heartbeat queue'

        self.heartbeat_test = {
            'component_name': self.alerter_name,
            'is_alive': True,
            'timestamp': datetime.datetime(2012, 1, 1).timestamp()
        }

        """
        ############# Alerts config base configuration ######################
        """
        self.enabled_alert = "True"
        self.critical_threshold_percentage = 95
        self.critical_threshold_seconds = 300
        self.critical_repeat_seconds = 300
        self.critical_enabled = "True"
        self.critical_repeat_enabled = "True"
        self.warning_threshold_percentage = 85
        self.warning_threshold_seconds = 200
        self.warning_enabled = "True"

        self.base_config = {
            "name": "base_percent_config",
            "enabled": self.enabled_alert,
            "parent_id": self.parent_id,
            "critical_threshold": self.critical_threshold_percentage,
            "critical_repeat": self.critical_repeat_seconds,
            "critical_repeat_enabled": self.critical_repeat_enabled,
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
            self.dummy_logger,
            self.rabbitmq,
            ALERTER_PUBLISHING_QUEUE_SIZE
        )

        """
        ############# Alerts config warning alerts disabled ####################
        """

        self.base_config['warning_enabled'] = str(
            not bool(self.warning_enabled))
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
            self.dummy_logger,
            self.rabbitmq,
            ALERTER_PUBLISHING_QUEUE_SIZE
        )

        """
        ############# Alerts config critical alerts disabled ###################
        """
        self.base_config['warning_enabled'] = self.warning_enabled
        self.base_config['critical_enabled'] = str(
            not bool(self.critical_enabled))
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
            self.dummy_logger,
            self.rabbitmq,
            ALERTER_PUBLISHING_QUEUE_SIZE
        )

        """
        ########## Alerts config critical repeat alerts disabled ###############
        """
        self.base_config['warning_enabled'] = self.warning_enabled
        self.base_config['critical_enabled'] = self.critical_enabled
        self.base_config['critical_repeat_enabled'] = str(
            not bool(self.critical_repeat_enabled))
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

        self.system_alerts_config_critical_repeat_disabled = SystemAlertsConfig(
            self.parent_id,
            self.open_file_descriptors,
            self.system_cpu_usage,
            self.system_storage_usage,
            self.system_ram_usage,
            self.system_is_down
        )

        self.test_system_alerter_critical_repeat_disabled = SystemAlerter(
            self.alerter_name,
            self.system_alerts_config_critical_repeat_disabled,
            self.dummy_logger,
            self.rabbitmq,
            ALERTER_PUBLISHING_QUEUE_SIZE
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
            self.dummy_logger,
            self.rabbitmq,
            ALERTER_PUBLISHING_QUEUE_SIZE
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
        try:
            self.test_system_alerter.rabbitmq.connect()
            self.test_system_alerter.rabbitmq.exchange_declare(
                HEALTH_CHECK_EXCHANGE, TOPIC, False, True, False, False)
            self.test_system_alerter.rabbitmq.exchange_declare(
                ALERT_EXCHANGE, TOPIC, False, True, False, False)
        except Exception as e:
            print("Setup failed: {}".format(e))

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        try:
            self.test_system_alerter.rabbitmq.connect()
            self.test_rabbit_manager.connect()
            # Declare the queues incase they aren't there, not to error
            self.test_system_alerter.rabbitmq.queue_declare(
                queue=self.target_queue_used, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.test_system_alerter.rabbitmq.queue_declare(
                queue=self.queue_used, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )

            self.test_system_alerter.rabbitmq.queue_purge(self.queue_used)
            self.test_system_alerter.rabbitmq.queue_purge(
                self.target_queue_used)
            self.test_system_alerter.rabbitmq.queue_delete(self.queue_used)
            self.test_system_alerter.rabbitmq.queue_delete(
                self.target_queue_used)
            self.test_system_alerter.rabbitmq.exchange_delete(
                HEALTH_CHECK_EXCHANGE)
            self.test_system_alerter.rabbitmq.exchange_delete(ALERT_EXCHANGE)
            self.test_system_alerter.rabbitmq.disconnect()
            self.test_rabbit_manager.disconnect()
        except Exception as e:
            print("Test failed: {}".format(e))

        self.dummy_logger = None
        self.rabbitmq = None
        self.publishing_queue = None
        self.test_system_alerter = None
        self.test_system_alerter_warnings_disabled = None
        self.test_system_alerter_critical_disabled = None
        self.test_system_alerter_all_disabled = None
        self.test_system_alerter_critical_repeat_disabled = None
        self.system_alerts_config = None
        self.system_alerts_config_warnings_disabled = None
        self.system_alerts_config_critical_disabled = None
        self.system_alerts_config_all_disabled = None
        self.system_alerts_config_critical_repeat_disabled = None
        self.test_system_alerter = None

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

    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert",
        autospec=True)
    def test_initial_run_no_increase_alerts_or_decrease_alerts(
            self, mock_storage_usage_decrease, mock_storage_usage_increase,
            mock_ram_usage_decrease, mock_ram_usage_increase,
            mock_cpu_usage_decrease, mock_cpu_usage_increase,
            mock_ofd_decrease, mock_ofd_increase) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_storage_usage_decrease.assert_not_called()
            mock_storage_usage_increase.assert_not_called()
            mock_ram_usage_decrease.assert_not_called()
            mock_ram_usage_increase.assert_not_called()
            mock_cpu_usage_decrease.assert_not_called()
            mock_cpu_usage_increase.assert_not_called()
            mock_ofd_decrease.assert_not_called()
            mock_ofd_increase.assert_not_called()

            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert",
        autospec=True)
    def test_initial_run_no_alerts_second_run_no_alerts(
            self, mock_storage_usage_decrease, mock_storage_usage_increase,
            mock_ram_usage_decrease, mock_ram_usage_increase,
            mock_cpu_usage_decrease, mock_cpu_usage_increase,
            mock_ofd_decrease, mock_ofd_increase) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_storage_usage_decrease.assert_not_called()
            mock_storage_usage_increase.assert_not_called()
            mock_ram_usage_decrease.assert_not_called()
            mock_ram_usage_increase.assert_not_called()
            mock_cpu_usage_decrease.assert_not_called()
            mock_cpu_usage_increase.assert_not_called()
            mock_ofd_decrease.assert_not_called()
            mock_ofd_increase.assert_not_called()

            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_storage_usage_decrease.assert_not_called()
            mock_storage_usage_increase.assert_not_called()
            mock_ram_usage_decrease.assert_not_called()
            mock_ram_usage_increase.assert_not_called()
            mock_cpu_usage_decrease.assert_not_called()
            mock_cpu_usage_increase.assert_not_called()
            mock_ofd_decrease.assert_not_called()
            mock_ofd_increase.assert_not_called()

            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @parameterized.expand([
        ('open_file_descriptors', 'mock_ofd_increase', '46', 'self.warning'),
        ('open_file_descriptors', 'mock_ofd_increase', '56', 'self.critical'),
        ('system_cpu_usage', 'mock_cpu_usage_increase', '46', 'self.warning'),
        ('system_cpu_usage', 'mock_cpu_usage_increase', '56', 'self.critical'),
        ('system_ram_usage', 'mock_ram_usage_increase', '46', 'self.warning'),
        ('system_ram_usage', 'mock_ram_usage_increase', '56', 'self.critical'),
        ('system_storage_usage', 'mock_storage_usage_increase', '46',
         'self.warning'),
        ('system_storage_usage', 'mock_storage_usage_increase', '56',
         'self.critical'),
    ])
    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert",
        autospec=True)
    def test_initial_run_no_increase_or_decrease_alerts_then_warning_or_critical_alert(
            self, metric_param, mock_param, mock_pad, mock_severity,
            mock_storage_usage_decrease, mock_storage_usage_increase,
            mock_ram_usage_decrease, mock_ram_usage_increase,
            mock_cpu_usage_decrease, mock_cpu_usage_increase,
            mock_ofd_decrease, mock_ofd_increase) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_storage_usage_decrease.assert_not_called()
            mock_storage_usage_increase.assert_not_called()
            mock_ram_usage_decrease.assert_not_called()
            mock_ram_usage_increase.assert_not_called()
            mock_cpu_usage_decrease.assert_not_called()
            mock_cpu_usage_increase.assert_not_called()
            mock_ofd_decrease.assert_not_called()
            mock_ofd_increase.assert_not_called()

            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data[metric_param]['current'] = self.percent_usage + int(mock_pad)
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_storage_usage_decrease.assert_not_called()
            mock_ram_usage_decrease.assert_not_called()
            mock_cpu_usage_decrease.assert_not_called()
            mock_ofd_decrease.assert_not_called()

            eval(mock_param).assert_called_once_with(
                self.system_name, data[metric_param]['current'],
                eval(mock_severity), meta_data['last_monitored'],
                eval(mock_severity),
                self.parent_id, self.system_id
            )

            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(SystemAlerter, "_classify_alert")
    def test_alerts_initial_run_warning_alerts_count_classify_alert(
            self, mock_classify_alert) -> None:
        data_for_alerting = []
        data = self.data_received_initially_warning_alert['result']['data']
        meta_data = self.data_received_initially_warning_alert['result'][
            'meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            self.assertEqual(4, mock_classify_alert.call_count)
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @parameterized.expand([
        ('open_file_descriptors', 'mock_ofd_increase', '46', 'self.warning'),
        ('open_file_descriptors', 'mock_ofd_increase', '56', 'self.critical'),
        ('system_cpu_usage', 'mock_cpu_usage_increase', '46', 'self.warning'),
        ('system_cpu_usage', 'mock_cpu_usage_increase', '56', 'self.critical'),
        ('system_ram_usage', 'mock_ram_usage_increase', '46', 'self.warning'),
        ('system_ram_usage', 'mock_ram_usage_increase', '56', 'self.critical'),
        ('system_storage_usage', 'mock_storage_usage_increase', '46',
         'self.warning'),
        ('system_storage_usage', 'mock_storage_usage_increase', '56',
         'self.critical'),
    ])
    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert",
        autospec=True)
    def test_initial_run_alerts_above_warning_and_critical_threshold(
            self, metric_param, mock_param, mock_pad, mock_severity,
            mock_storage_usage_decrease, mock_storage_usage_increase,
            mock_ram_usage_decrease, mock_ram_usage_increase,
            mock_cpu_usage_decrease, mock_cpu_usage_increase,
            mock_ofd_decrease, mock_ofd_increase) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data[metric_param]['current'] = self.percent_usage + int(mock_pad)
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_storage_usage_decrease.assert_not_called()
            mock_ram_usage_decrease.assert_not_called()
            mock_cpu_usage_decrease.assert_not_called()
            mock_ofd_decrease.assert_not_called()
            eval(mock_param).assert_called_once_with(
                self.system_name, data[metric_param]['current'],
                eval(mock_severity), meta_data['last_monitored'],
                eval(mock_severity), self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @parameterized.expand([
        ('open_file_descriptors', 'mock_ofd_increase', 'mock_ofd_decrease'),
        ('system_cpu_usage', 'mock_cpu_usage_increase',
         'mock_cpu_usage_decrease'),
        ('system_ram_usage', 'mock_ram_usage_increase',
         'mock_ram_usage_decrease'),
        ('system_storage_usage', 'mock_storage_usage_increase',
         'mock_storage_usage_decrease'),
    ])
    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert",
        autospec=True)
    def test_initial_run_warning_alert_then_info_alert_on_decrease(
            self, metric_param, mock_param, mock_param_2,
            mock_storage_usage_decrease, mock_storage_usage_increase,
            mock_ram_usage_decrease, mock_ram_usage_increase,
            mock_cpu_usage_decrease, mock_cpu_usage_increase,
            mock_ofd_decrease, mock_ofd_increase) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data[metric_param]['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_storage_usage_decrease.assert_not_called()
            mock_ram_usage_decrease.assert_not_called()
            mock_cpu_usage_decrease.assert_not_called()
            mock_ofd_decrease.assert_not_called()
            eval(mock_param).assert_called_once_with(
                self.system_name, data[metric_param]['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data[metric_param]['current'] = self.percent_usage + 36
        data[metric_param]['previous'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            eval(mock_param_2).assert_called_once_with(
                self.system_name, data[metric_param]['current'],
                self.info, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @parameterized.expand([
        ('open_file_descriptors', 'mock_ofd_increase'),
        ('system_cpu_usage', 'mock_cpu_usage_increase'),
        ('system_ram_usage', 'mock_ram_usage_increase'),
        ('system_storage_usage', 'mock_storage_usage_increase'),
    ])
    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert",
        autospec=True)
    def test_initial_run_warning_alert_then_critical_alert(
            self, metric_param, mock_param, mock_storage_usage_decrease,
            mock_storage_usage_increase, mock_ram_usage_decrease,
            mock_ram_usage_increase, mock_cpu_usage_decrease,
            mock_cpu_usage_increase, mock_ofd_decrease,
            mock_ofd_increase) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data[metric_param]['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_storage_usage_decrease.assert_not_called()
            mock_ram_usage_decrease.assert_not_called()
            mock_cpu_usage_decrease.assert_not_called()
            mock_ofd_decrease.assert_not_called()
            eval(mock_param).assert_called_once_with(
                self.system_name, data[metric_param]['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data[metric_param]['current'] = self.percent_usage + 56
        data[metric_param]['previous'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_storage_usage_decrease.assert_not_called()
            mock_ram_usage_decrease.assert_not_called()
            mock_cpu_usage_decrease.assert_not_called()
            mock_ofd_decrease.assert_not_called()
            eval(mock_param).assert_called_with(
                self.system_name, data[metric_param]['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @parameterized.expand([
        ('open_file_descriptors', 'mock_ofd_increase'),
        ('system_cpu_usage', 'mock_cpu_usage_increase'),
        ('system_ram_usage', 'mock_ram_usage_increase'),
        ('system_storage_usage', 'mock_storage_usage_increase'),
    ])
    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert",
        autospec=True)
    def test_initial_run_warning_alerts_then_increase_in_warning_no_alert(
            self, metric_param, mock_param, mock_storage_usage_decrease,
            mock_storage_usage_increase, mock_ram_usage_decrease,
            mock_ram_usage_increase, mock_cpu_usage_decrease,
            mock_cpu_usage_increase, mock_ofd_decrease,
            mock_ofd_increase) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data[metric_param]['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_storage_usage_decrease.assert_not_called()
            mock_ram_usage_decrease.assert_not_called()
            mock_cpu_usage_decrease.assert_not_called()
            mock_ofd_decrease.assert_not_called()
            eval(mock_param).assert_called_once_with(
                self.system_name, data[metric_param]['current'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data[metric_param]['current'] = self.percent_usage + 47
        data[metric_param]['previous'] = self.percent_usage + 46
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_storage_usage_decrease.assert_not_called()
            mock_ram_usage_decrease.assert_not_called()
            mock_cpu_usage_decrease.assert_not_called()
            mock_ofd_decrease.assert_not_called()
            eval(mock_param).assert_called_once_with(
                self.system_name, data[metric_param]['previous'],
                self.warning, meta_data['last_monitored'], self.warning,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @parameterized.expand([
        ('open_file_descriptors', 'mock_ofd_increase', 'mock_ofd_decrease'),
        ('system_cpu_usage', 'mock_cpu_usage_increase',
         'mock_cpu_usage_decrease'),
        ('system_ram_usage', 'mock_ram_usage_increase',
         'mock_ram_usage_decrease'),
        ('system_storage_usage', 'mock_storage_usage_increase',
         'mock_storage_usage_decrease'),
    ])
    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert",
        autospec=True)
    def test_critical_alerts_then_no_increase_alerts_on_decrease_between_critical_and_warning(
            self, metric_param, mock_param, mock_param_2,
            mock_storage_usage_decrease, mock_storage_usage_increase,
            mock_ram_usage_decrease, mock_ram_usage_increase,
            mock_cpu_usage_decrease, mock_cpu_usage_increase,
            mock_ofd_decrease, mock_ofd_increase) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data[metric_param]['current'] = self.percent_usage + 56
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_storage_usage_decrease.assert_not_called()
            mock_ram_usage_decrease.assert_not_called()
            mock_cpu_usage_decrease.assert_not_called()
            mock_ofd_decrease.assert_not_called()

            eval(mock_param).assert_called_once_with(
                self.system_name, data[metric_param]['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )

            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data[metric_param]['current'] = self.percent_usage + 50
        data[metric_param]['previous'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            eval(mock_param_2).assert_called_once_with(
                self.system_name, data[metric_param]['current'],
                self.info, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            eval(mock_param).assert_called_once_with(
                self.system_name, data[metric_param]['previous'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )

            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @parameterized.expand([
        ('open_file_descriptors', 'mock_ofd_increase'),
        ('system_cpu_usage', 'mock_cpu_usage_increase'),
        ('system_ram_usage', 'mock_ram_usage_increase'),
        ('system_storage_usage', 'mock_storage_usage_increase'),
    ])
    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.TimedTaskLimiter.last_time_that_did_task",
        autospec=True)
    def test_critical_alerts_then_no_alerts_before_repeat_timer_elapsed(
            self, metric_param, mock_param, mock_last_time_that_did_task,
            mock_storage_usage_decrease, mock_storage_usage_increase,
            mock_ram_usage_decrease, mock_ram_usage_increase,
            mock_cpu_usage_decrease, mock_cpu_usage_increase,
            mock_ofd_decrease, mock_ofd_increase) -> None:
        mock_last_time_that_did_task.return_value = self.last_monitored
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data[metric_param]['current'] = self.percent_usage + 56
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_storage_usage_decrease.assert_not_called()
            mock_ram_usage_decrease.assert_not_called()
            mock_cpu_usage_decrease.assert_not_called()
            mock_ofd_decrease.assert_not_called()
            eval(mock_param).assert_called_once_with(
                self.system_name, data[metric_param]['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data[metric_param]['current'] = self.percent_usage + 58
        data[metric_param]['previous'] = self.percent_usage + 56
        meta_data['last_monitored'] = self.last_monitored + \
                                      self.critical_repeat_seconds - 1
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_storage_usage_decrease.assert_not_called()
            mock_ram_usage_decrease.assert_not_called()
            mock_cpu_usage_decrease.assert_not_called()
            mock_ofd_decrease.assert_not_called()
            eval(mock_param).assert_called_once_with(
                self.system_name, data[metric_param]['previous'],
                self.critical, self.last_monitored, self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @parameterized.expand([
        ('open_file_descriptors', 'mock_ofd_increase'),
        ('system_cpu_usage', 'mock_cpu_usage_increase'),
        ('system_ram_usage', 'mock_ram_usage_increase'),
        ('system_storage_usage', 'mock_storage_usage_increase'),
    ])
    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.TimedTaskLimiter.last_time_that_did_task",
        autospec=True)
    def test_critical_alerts_then_critical_alert_on_same_value_after_repeat_timer_elapsed(
            self, metric_param, mock_param, mock_last_time_that_did_task,
            mock_storage_usage_decrease, mock_storage_usage_increase,
            mock_ram_usage_decrease, mock_ram_usage_increase,
            mock_cpu_usage_decrease, mock_cpu_usage_increase,
            mock_ofd_decrease, mock_ofd_increase) -> None:
        mock_last_time_that_did_task.return_value = self.last_monitored
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data[metric_param]['current'] = self.percent_usage + 56
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_storage_usage_decrease.assert_not_called()
            mock_ram_usage_decrease.assert_not_called()
            mock_cpu_usage_decrease.assert_not_called()
            mock_ofd_decrease.assert_not_called()
            eval(mock_param).assert_called_once_with(
                self.system_name, data[metric_param]['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        meta_data['last_monitored'] = self.last_monitored + \
                                      self.critical_repeat_seconds
        data[metric_param]['current'] = self.percent_usage + 56
        data[metric_param]['previous'] = self.percent_usage + 56
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_storage_usage_decrease.assert_not_called()
            mock_ram_usage_decrease.assert_not_called()
            mock_cpu_usage_decrease.assert_not_called()
            mock_ofd_decrease.assert_not_called()
            eval(mock_param).assert_called_with(
                self.system_name, data[metric_param]['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @parameterized.expand([
        ('open_file_descriptors', 'mock_ofd_increase'),
        ('system_cpu_usage', 'mock_cpu_usage_increase'),
        ('system_ram_usage', 'mock_ram_usage_increase'),
        ('system_storage_usage', 'mock_storage_usage_increase'),
    ])
    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.TimedTaskLimiter.last_time_that_did_task",
        autospec=True)
    def test_critical_alerts_then_critical_alert_on_lower_value_after_repeat_timer_elapsed(
            self, metric_param, mock_param, mock_last_time_that_did_task,
            mock_storage_usage_decrease, mock_storage_usage_increase,
            mock_ram_usage_decrease, mock_ram_usage_increase,
            mock_cpu_usage_decrease, mock_cpu_usage_increase,
            mock_ofd_decrease, mock_ofd_increase) -> None:
        mock_last_time_that_did_task.return_value = self.last_monitored
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data[metric_param]['current'] = self.percent_usage + 57
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            eval(mock_param).assert_called_once_with(
                self.system_name, data[metric_param]['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        meta_data['last_monitored'] = self.last_monitored + \
                                      self.critical_repeat_seconds
        data[metric_param]['current'] = self.percent_usage + 56
        data[metric_param]['previous'] = self.percent_usage + 57
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_results(data, meta_data,
                                                  data_for_alerting)
        try:
            eval(mock_param).assert_called_with(
                self.system_name, data[metric_param]['current'],
                self.critical, meta_data['last_monitored'], self.critical,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemBackUpAgainAlert",
                autospec=True)
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

    @mock.patch("src.alerter.alerters.system.SystemBackUpAgainAlert",
                autospec=True)
    def test_system_back_up_alert(self, mock_system_back_up) -> None:
        data_for_alerting = []
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._system_initial_alert_sent[
            self.system_id][
            GroupedSystemAlertsMetricCode.SystemIsDown.value] = True
        data = self.data_received_initially_no_alert['result']['data']
        data['went_down_at']['previous'] = self.last_monitored
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_system_back_up.assert_called_once_with(
                self.system_name, self.info, self.last_monitored,
                self.parent_id, self.system_id
            )
            # There are extra alerts due to initial start-up alerts
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.TimedTaskLimiter.reset",
                autospec=True)
    def test_system_back_up_timed_task_limiter_reset(self, mock_reset) -> None:
        data_for_alerting = []
        self.test_system_alerter._create_state_for_system(self.system_id)
        # Set that the initial downtime alert was sent already
        self.test_system_alerter._system_initial_alert_sent[
            self.system_id][
            GroupedSystemAlertsMetricCode.SystemIsDown.value] = True
        data = self.data_received_initially_no_alert['result']['data']
        data['went_down_at']['previous'] = self.last_monitored
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_reset.assert_called_once()
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemWentDownAtAlert",
                autospec=True)
    def test_system_went_down_at_no_alert_below_warning_threshold(
            self, mock_system_is_down) -> None:
        data_for_alerting = []
        data = self.data_received_error_data['error']
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_errors(data, data_for_alerting)
        try:
            mock_system_is_down.assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    """
    These tests assume that critical_threshold_seconds > warning_threshold_seconds
    """

    @mock.patch("src.alerter.alerters.system.SystemWentDownAtAlert",
                autospec=True)
    def test_system_went_down_at_alert_above_warning_threshold(
            self, mock_system_is_down) -> None:
        data_for_alerting = []
        data = self.data_received_error_data['error']
        data['meta_data']['time'] = self.last_monitored + \
                                    self.warning_threshold_seconds
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_errors(data, data_for_alerting)
        try:
            mock_system_is_down.assert_called_once_with(
                self.system_name, self.warning, data['meta_data']['time'],
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemWentDownAtAlert",
                autospec=True)
    def test_system_went_down_at_alert_above_critical_threshold(
            self, mock_system_is_down) -> None:
        data_for_alerting = []
        data = self.data_received_error_data['error']
        data['meta_data']['time'] = self.last_monitored + \
                                    self.critical_threshold_seconds
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_errors(data, data_for_alerting)
        try:
            mock_system_is_down.assert_called_once_with(
                self.system_name, self.critical, data['meta_data']['time'],
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStillDownAlert",
                autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemWentDownAtAlert",
                autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.TimedTaskLimiter.last_time_that_did_task",
        autospec=True)
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

        data['meta_data'][
            'time'] = past_warning_time + self.critical_repeat_seconds - 1
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

    @mock.patch("src.alerter.alerters.system.SystemStillDownAlert",
                autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemWentDownAtAlert",
                autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.TimedTaskLimiter.last_time_that_did_task",
        autospec=True)
    def test_system_went_down_at_alert_above_warning_threshold_then_critical_repeat(
            self, mock_last_time_did_task, mock_system_is_down,
            mock_system_still_down) -> None:
        data_for_alerting = []
        data = self.data_received_error_data['error']
        past_warning_time = self.last_monitored + self.warning_threshold_seconds
        mock_last_time_did_task.return_value = past_warning_time
        data['meta_data']['time'] = past_warning_time
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_errors(data, data_for_alerting)
        try:
            mock_system_is_down.assert_called_once_with(
                self.system_name, self.warning, past_warning_time,
                self.parent_id, self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['meta_data'][
            'time'] = past_warning_time + self.critical_repeat_seconds
        downtime = int(data['meta_data']['time'] - self.last_monitored)
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_errors(data, data_for_alerting)
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
            self.assertEqual(3, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStillDownAlert",
                autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemWentDownAtAlert",
                autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.TimedTaskLimiter.last_time_that_did_task",
        autospec=True)
    def test_system_went_down_at_alert_above_critical_threshold_then_no_critical_repeat(
            self, mock_last_time_did_task, mock_system_is_down,
            mock_system_still_down) -> None:
        data_for_alerting = []
        data = self.data_received_error_data['error']
        past_critical_time = self.last_monitored + self.critical_threshold_seconds
        mock_last_time_did_task.return_value = past_critical_time
        data['meta_data']['time'] = past_critical_time
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_errors(data, data_for_alerting)
        try:
            mock_system_is_down.assert_called_once_with(
                self.system_name, self.critical, past_critical_time,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['meta_data'][
            'time'] = past_critical_time + self.critical_repeat_seconds - 1
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_errors(data, data_for_alerting)
        try:
            mock_system_is_down.assert_called_once_with(
                self.system_name, self.critical, past_critical_time,
                self.parent_id, self.system_id
            )
            mock_system_still_down.assert_not_called()
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemStillDownAlert",
                autospec=True)
    @mock.patch("src.alerter.alerters.system.SystemWentDownAtAlert",
                autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.TimedTaskLimiter.last_time_that_did_task",
        autospec=True)
    def test_system_went_down_at_alert_above_warning_threshold_then_critical_repeat(
            self, mock_last_time_did_task, mock_system_is_down,
            mock_system_still_down) -> None:
        data_for_alerting = []
        data = self.data_received_error_data['error']
        past_critical_time = self.last_monitored + self.critical_threshold_seconds
        mock_last_time_did_task.return_value = past_critical_time
        data['meta_data']['time'] = past_critical_time
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_errors(data, data_for_alerting)
        try:
            mock_system_is_down.assert_called_once_with(
                self.system_name, self.critical, past_critical_time,
                self.parent_id, self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data['meta_data'][
            'time'] = past_critical_time + self.critical_repeat_seconds
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

    @mock.patch("src.alerter.alerters.system.MetricNotFoundErrorAlert",
                autospec=True)
    def test_process_errors_metric_not_found_alert(self, mock_alert) -> None:
        data_for_alerting = []
        data = self.data_received_error_data['error']
        data['code'] = 5003
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_errors(data, data_for_alerting)
        try:
            mock_alert.assert_called_once_with(
                self.system_name, data['message'], self.error,
                data['meta_data']['time'], self.parent_id,
                self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.MetricFoundAlert",
                autospec=True)
    @mock.patch("src.alerter.alerters.system.MetricNotFoundErrorAlert",
                autospec=True)
    def test_process_error_metric_not_found_alert_metric_found_alert(self,
                                                                     mock_alert_not_found,
                                                                     mock_alert_found) -> None:

        data_for_alerting = []
        data = self.data_received_error_data['error']
        data['code'] = 5003
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_errors(data, data_for_alerting)
        try:
            mock_alert_not_found.assert_called_once_with(
                self.system_name, data['message'], self.error,
                data['meta_data']['time'], self.parent_id,
                self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data = self.data_received_error_data['error']
        data['code'] = 600000000  # This code doesn't exist
        self.test_system_alerter._process_errors(data, data_for_alerting)
        try:
            mock_alert_found.assert_called_once_with(
                self.system_name, "Metrics have been found!", self.info,
                data['meta_data']['time'], self.parent_id,
                self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.MetricFoundAlert",
                autospec=True)
    @mock.patch("src.alerter.alerters.system.MetricNotFoundErrorAlert",
                autospec=True)
    def test_process_error_metric_not_found_alert_process_result_metric_found_alert(
            self,
            mock_alert_not_found, mock_alert_found) -> None:

        data_for_alerting = []
        data = self.data_received_error_data['error']
        data['code'] = 5003
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_errors(data, data_for_alerting)
        try:
            mock_alert_not_found.assert_called_once_with(
                self.system_name, data['message'], self.error,
                data['meta_data']['time'], self.parent_id,
                self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._process_results(data, meta_data,
                                                  data_for_alerting)
        try:
            mock_alert_found.assert_called_once_with(
                self.system_name, "Metrics have been found!", self.info,
                meta_data['last_monitored'], self.parent_id,
                self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.InvalidUrlAlert", autospec=True)
    def test_process_errors_invalid_url_alert(self, mock_alert) -> None:
        data_for_alerting = []
        data = self.data_received_error_data['error']
        data['code'] = 5009
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_errors(data, data_for_alerting)
        try:
            mock_alert.assert_called_once_with(
                self.system_name, data['message'], self.error,
                data['meta_data']['time'], self.parent_id,
                self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.ValidUrlAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.InvalidUrlAlert", autospec=True)
    def test_process_errors_invalid_url_alert_then_valid_url_alert(self,
                                                                   mock_alert_invalid,
                                                                   mock_alert_valid) -> None:
        data_for_alerting = []
        data = self.data_received_error_data['error']
        data['code'] = 5009
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_errors(data, data_for_alerting)
        try:
            mock_alert_invalid.assert_called_once_with(
                self.system_name, data['message'], self.error,
                data['meta_data']['time'], self.parent_id,
                self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))
        data = self.data_received_error_data['error']
        data['code'] = 600000000  # This code doesn't exist
        self.test_system_alerter._process_errors(data, data_for_alerting)
        try:
            mock_alert_valid.assert_called_once_with(
                self.system_name, "Url is valid!", self.info,
                data['meta_data']['time'], self.parent_id,
                self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.ValidUrlAlert", autospec=True)
    @mock.patch("src.alerter.alerters.system.InvalidUrlAlert", autospec=True)
    def test_process_errors_invalid_url_alert_then_process_results_valid_url_alert(
            self,
            mock_alert_invalid, mock_alert_valid) -> None:
        data_for_alerting = []
        data = self.data_received_error_data['error']
        data['code'] = 5009
        self.test_system_alerter._create_state_for_system(self.system_id)
        self.test_system_alerter._process_errors(data, data_for_alerting)
        try:
            mock_alert_invalid.assert_called_once_with(
                self.system_name, data['message'], self.error,
                data['meta_data']['time'], self.parent_id,
                self.system_id
            )
            self.assertEqual(1, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

        data = self.data_received_initially_no_alert['result']['data']
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter._process_results(data, meta_data,
                                                  data_for_alerting)
        try:
            mock_alert_valid.assert_called_once_with(
                self.system_name, "Url is valid!", self.info,
                meta_data['last_monitored'], self.parent_id,
                self.system_id
            )
            self.assertEqual(2, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(SystemAlerter, "_classify_alert")
    def test_alerts_warning_alerts_disabled_metric_above_warning_threshold(
            self, mock_classify_alert) -> None:
        data_for_alerting = []
        data = self.data_received_initially_warning_alert['result']['data']
        meta_data = self.data_received_initially_warning_alert['result'][
            'meta_data']
        self.test_system_alerter_warnings_disabled._create_state_for_system(
            self.system_id)
        self.test_system_alerter_warnings_disabled._process_results(
            data, meta_data, data_for_alerting)
        try:
            self.assertEqual(4, mock_classify_alert.call_count)
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @parameterized.expand([
        ('open_file_descriptors', 'mock_ofd_increase'),
        ('system_cpu_usage', 'mock_cpu_usage_increase'),
        ('system_ram_usage', 'mock_ram_usage_increase'),
        ('system_storage_usage', 'mock_storage_usage_increase'),
    ])
    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert",
        autospec=True)
    def test_warning_alerts_disabled_increase_above_warning_threshold_no_alerts_occur(
            self, metric_param, mock_param, mock_storage_usage_decrease,
            mock_storage_usage_increase, mock_ram_usage_decrease,
            mock_ram_usage_increase, mock_cpu_usage_decrease,
            mock_cpu_usage_increase, mock_ofd_decrease,
            mock_ofd_increase) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data[metric_param]['current'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter_warnings_disabled._create_state_for_system(
            self.system_id)
        self.test_system_alerter_warnings_disabled._process_results(
            data, meta_data, data_for_alerting)
        try:
            mock_storage_usage_decrease.assert_not_called()
            mock_ram_usage_decrease.assert_not_called()
            mock_cpu_usage_decrease.assert_not_called()
            mock_ofd_decrease.assert_not_called()

            eval(mock_param).assert_not_called()
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(SystemAlerter, "_classify_alert")
    def test_alerts_critical_alerts_disabled_metric_above_critical_threshold(
            self, mock_classify_alert) -> None:
        data_for_alerting = []
        data = self.data_received_initially_warning_alert['result']['data']
        meta_data = self.data_received_initially_warning_alert['result'][
            'meta_data']
        self.test_system_alerter_critical_disabled._create_state_for_system(
            self.system_id)
        self.test_system_alerter_critical_disabled._process_results(
            data, meta_data, data_for_alerting)
        try:
            self.assertEqual(4, mock_classify_alert.call_count)
            self.assertEqual(0, len(data_for_alerting))
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @parameterized.expand([
        ('open_file_descriptors', 'mock_ofd_increase'),
        ('system_cpu_usage', 'mock_cpu_usage_increase'),
        ('system_ram_usage', 'mock_ram_usage_increase'),
        ('system_storage_usage', 'mock_storage_usage_increase'),
    ])
    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert",
        autospec=True)
    def test_critical_alerts_disabled_increase_above_critical_threshold_warning_alert(
            self, metric_param, mock_param, mock_storage_usage_decrease,
            mock_storage_usage_increase, mock_ram_usage_decrease,
            mock_ram_usage_increase, mock_cpu_usage_decrease,
            mock_cpu_usage_increase, mock_ofd_decrease,
            mock_ofd_increase) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data[metric_param]['current'] = self.percent_usage + 56
        data[metric_param]['previous'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter_critical_disabled._create_state_for_system(
            self.system_id)
        self.test_system_alerter_critical_disabled._process_results(
            data, meta_data, data_for_alerting)
        try:
            eval(mock_param).assert_called_once_with(
                self.system_name, data[metric_param]['current'],
                self.warning, meta_data['last_monitored'],
                self.warning, self.parent_id, self.system_id
            )
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @parameterized.expand([
        ('open_file_descriptors', 'mock_ofd_increase'),
        ('system_cpu_usage', 'mock_cpu_usage_increase'),
        ('system_ram_usage', 'mock_ram_usage_increase'),
        ('system_storage_usage', 'mock_storage_usage_increase'),
    ])
    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert",
        autospec=True)
    def test_increase_above_critical_first_time_critical_repeat_disabled(
            self, metric_param, mock_param, mock_storage_usage_decrease,
            mock_storage_usage_increase, mock_ram_usage_decrease,
            mock_ram_usage_increase, mock_cpu_usage_decrease,
            mock_cpu_usage_increase, mock_ofd_decrease,
            mock_ofd_increase) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data[metric_param]['current'] = self.percent_usage + 56
        data[metric_param]['previous'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter_critical_repeat_disabled._create_state_for_system(
            self.system_id)
        self.test_system_alerter_critical_repeat_disabled._process_results(
            data, meta_data, data_for_alerting)
        try:
            eval(mock_param).assert_called_once_with(
                self.system_name, data[metric_param]['current'],
                self.critical, meta_data['last_monitored'],
                self.critical, self.parent_id, self.system_id
            )
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @parameterized.expand([
        ('open_file_descriptors', 'mock_ofd_increase'),
        ('system_cpu_usage', 'mock_cpu_usage_increase'),
        ('system_ram_usage', 'mock_ram_usage_increase'),
        ('system_storage_usage', 'mock_storage_usage_increase'),
    ])
    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert",
        autospec=True)
    def test_increase_above_critical_second_time_critical_repeat_disabled(
            self, metric_param, mock_param, mock_storage_usage_decrease,
            mock_storage_usage_increase, mock_ram_usage_decrease,
            mock_ram_usage_increase, mock_cpu_usage_decrease,
            mock_cpu_usage_increase, mock_ofd_decrease,
            mock_ofd_increase) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data[metric_param]['current'] = self.percent_usage + 56
        data[metric_param]['previous'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter_critical_repeat_disabled._create_state_for_system(
            self.system_id)
        self.test_system_alerter_critical_repeat_disabled._process_results(
            data, meta_data, data_for_alerting)

        # process again to confirm that when critical_repeat is disabled, no
        # critical alerts are sent even if the repeat time passes.
        old_last_monitored = meta_data['last_monitored']
        meta_data['last_monitored'] = \
            old_last_monitored + self.critical_repeat_seconds
        self.test_system_alerter_critical_repeat_disabled._process_results(
            data, meta_data, data_for_alerting)
        try:
            eval(mock_param).assert_called_once_with(
                self.system_name, data[metric_param]['current'],
                self.critical, old_last_monitored,
                self.critical, self.parent_id, self.system_id
            )
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @parameterized.expand([
        ('open_file_descriptors', 'mock_ofd_increase'),
        ('system_cpu_usage', 'mock_cpu_usage_increase'),
        ('system_ram_usage', 'mock_ram_usage_increase'),
        ('system_storage_usage', 'mock_storage_usage_increase'),
    ])
    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.OpenFileDescriptorsDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemCPUUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemRAMUsageDecreasedBelowThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageIncreasedAboveThresholdAlert",
        autospec=True)
    @mock.patch(
        "src.alerter.alerters.system.SystemStorageUsageDecreasedBelowThresholdAlert",
        autospec=True)
    def test_critical_alerts_and_warning_alerts_disabled_increase_above_critical_threshold_no_alerts(
            self, metric_param, mock_param, mock_storage_usage_decrease,
            mock_storage_usage_increase, mock_ram_usage_decrease,
            mock_ram_usage_increase, mock_cpu_usage_decrease,
            mock_cpu_usage_increase, mock_ofd_decrease,
            mock_ofd_increase) -> None:
        data_for_alerting = []
        data = self.data_received_initially_no_alert['result']['data']
        data[metric_param]['current'] = self.percent_usage + 56
        data[metric_param]['previous'] = self.percent_usage + 46
        meta_data = self.data_received_initially_no_alert['result']['meta_data']
        self.test_system_alerter_all_disabled._create_state_for_system(
            self.system_id)
        self.test_system_alerter_all_disabled._process_results(
            data, meta_data, data_for_alerting)
        try:
            eval(mock_param).assert_not_called()
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(SystemAlerter, "_classify_alert")
    def test_alerts_all_alerts_disabled_metric_above_critical_threshold_and_warning_threshold(
            self, mock_classify_alert) -> None:
        data_for_alerting = []
        data = self.data_received_initially_critical_alert['result']['data']
        meta_data = self.data_received_initially_critical_alert['result'][
            'meta_data']
        self.test_system_alerter_all_disabled._create_state_for_system(
            self.system_id)
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
            self.rabbitmq.connect()
            self.rabbitmq.queue_declare(self.queue_used, passive=True)
        except pika.exceptions.ConnectionClosedByBroker:
            self.fail("Queue {} was not declared".format(self.queue_used))

    def test_initialise_rabbit_initialises_exchanges(self) -> None:
        self.test_system_alerter._initialise_rabbitmq()

        try:
            self.rabbitmq.connect()
            self.rabbitmq.exchange_declare(ALERT_EXCHANGE, passive=True)
        except pika.exceptions.ConnectionClosedByBroker:
            self.fail("Exchange {} was not declared".format(ALERT_EXCHANGE))

    def test_send_warning_alerts_correctly(
            self) -> None:
        try:
            self.test_system_alerter._initialise_rabbitmq()
            self.test_system_alerter.rabbitmq.queue_delete(
                self.target_queue_used)
            self.test_system_alerter.rabbitmq.exchange_declare(
                HEALTH_CHECK_EXCHANGE, TOPIC, False, True, False, False)
            res = self.test_system_alerter.rabbitmq.queue_declare(
                queue=self.target_queue_used, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_system_alerter.rabbitmq.queue_bind(
                queue=self.target_queue_used, exchange=ALERT_EXCHANGE,
                routing_key=self.output_routing_key)

            self.test_system_alerter.rabbitmq.basic_publish_confirm(
                exchange=ALERT_EXCHANGE,
                routing_key=self.output_routing_key,
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
            self.assertEqual(json.loads(json.dumps(self.alert.alert_data)),
                             json.loads(body))

            self.test_system_alerter.rabbitmq.queue_purge(
                self.target_queue_used)
            self.test_system_alerter.rabbitmq.queue_delete(
                self.target_queue_used)
            self.test_system_alerter.rabbitmq.exchange_delete(ALERT_EXCHANGE)
            self.test_system_alerter.rabbitmq.exchange_delete(
                HEALTH_CHECK_EXCHANGE)
            self.test_system_alerter.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    # Same test that is in monitors tests
    def test_send_heartbeat_sends_a_heartbeat_correctly(self) -> None:
        try:
            self.test_system_alerter._initialise_rabbitmq()
            self.test_system_alerter.rabbitmq.exchange_declare(
                HEALTH_CHECK_EXCHANGE, TOPIC, False, True, False, False)

            self.test_system_alerter.rabbitmq.queue_delete(self.heartbeat_queue)

            res = self.test_system_alerter.rabbitmq.queue_declare(
                queue=self.heartbeat_queue, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_system_alerter.rabbitmq.queue_bind(
                queue=self.heartbeat_queue, exchange=HEALTH_CHECK_EXCHANGE,
                routing_key=HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY)
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
            self.test_system_alerter.rabbitmq.exchange_delete(
                HEALTH_CHECK_EXCHANGE)
            self.test_system_alerter.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    """
    Testing _process_data using RabbitMQ
    """

    @mock.patch("src.alerter.alerters.system.SystemAlerter._process_results")
    @mock.patch(
        "src.alerter.alerters.system.SystemAlerter._create_state_for_system")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_result_data_no_alerts(
            self, mock_ack, mock_create_state_for_system,
            mock_process_results) -> None:

        mock_ack.return_value = None

        try:
            self.test_system_alerter.rabbitmq.connect()
            blocking_channel = self.test_system_alerter.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.input_routing_key)
            body = json.dumps(self.data_received_initially_no_alert)
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_create_state_for_system.assert_called_with(self.system_id)
            mock_process_results.assert_called_with(
                self.data_received_initially_no_alert['result']['data'],
                self.data_received_initially_no_alert['result']['meta_data'],
                []
            )
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemAlerter._process_errors")
    @mock.patch(
        "src.alerter.alerters.system.SystemAlerter._create_state_for_system")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_error_data_no_alerts(
            self, mock_ack, mock_create_state_for_system,
            mock_process_errors) -> None:

        mock_ack.return_value = None

        try:
            self.test_system_alerter.rabbitmq.connect()
            blocking_channel = self.test_system_alerter.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.input_routing_key)
            body = json.dumps(self.data_received_error_data)
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_create_state_for_system.assert_called_with(self.system_id)
            mock_process_errors.assert_called_with(
                self.data_received_error_data['error'],
                []
            )
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._send_heartbeat")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._process_results")
    @mock.patch(
        "src.alerter.alerters.system.SystemAlerter._create_state_for_system")
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
                routing_key=self.input_routing_key)
            body = json.dumps(self.data_received_initially_no_alert)
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            heartbeat_test = {
                'component_name': self.alerter_name,
                'is_alive': True,
                'timestamp': datetime.datetime(2012, 1, 1).timestamp()
            }
            mock_send_heartbeat.assert_called_with(heartbeat_test)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._send_heartbeat")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._process_errors")
    @mock.patch(
        "src.alerter.alerters.system.SystemAlerter._create_state_for_system")
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
                routing_key=self.input_routing_key)
            body = json.dumps(self.data_received_error_data)
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            heartbeat_test = {
                'component_name': self.alerter_name,
                'is_alive': True,
                'timestamp': datetime.datetime(2012, 1, 1).timestamp()
            }
            mock_send_heartbeat.assert_called_with(heartbeat_test)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._send_heartbeat")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._process_results")
    @mock.patch(
        "src.alerter.alerters.system.SystemAlerter._create_state_for_system")
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
                routing_key=self.bad_output_routing_key)
            body = json.dumps(self.data_received_initially_no_alert)
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_send_heartbeat.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._send_heartbeat")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._process_errors")
    @mock.patch(
        "src.alerter.alerters.system.SystemAlerter._create_state_for_system")
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
                routing_key=self.bad_output_routing_key)
            body = json.dumps(self.data_received_error_data)
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_send_heartbeat.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemAlerter._send_data")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._process_results")
    @mock.patch(
        "src.alerter.alerters.system.SystemAlerter._create_state_for_system")
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
                routing_key=self.input_routing_key)
            body = json.dumps(self.data_received_initially_no_alert)
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_send_data.assert_called_once()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemAlerter._send_data")
    @mock.patch("src.alerter.alerters.system.SystemAlerter._process_errors")
    @mock.patch(
        "src.alerter.alerters.system.SystemAlerter._create_state_for_system")
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
                routing_key=self.input_routing_key)
            body = json.dumps(self.data_received_error_data)
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_send_data.assert_called_once()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemAlerter._process_results")
    @mock.patch(
        "src.alerter.alerters.system.SystemAlerter._create_state_for_system")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_result_data_not_processed_bad_routing_key(
            self, mock_ack, mock_create_state_for_system,
            mock_process_results) -> None:
        mock_ack.return_value = None
        try:
            self.test_system_alerter.rabbitmq.connect()
            blocking_channel = self.test_system_alerter.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.bad_output_routing_key)
            body = json.dumps(self.data_received_initially_no_alert)
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_create_state_for_system.assert_not_called()
            mock_process_results.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemAlerter._process_errors")
    @mock.patch(
        "src.alerter.alerters.system.SystemAlerter._create_state_for_system")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_error_data_not_processed_bad_routing_key(
            self, mock_ack, mock_create_state_for_system,
            mock_process_errors) -> None:

        mock_ack.return_value = None

        try:
            self.test_system_alerter.rabbitmq.connect()
            blocking_channel = self.test_system_alerter.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.bad_output_routing_key)
            body = json.dumps(self.data_received_error_data)
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_create_state_for_system.assert_not_called()
            mock_process_errors.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemAlerter._process_results")
    @mock.patch(
        "src.alerter.alerters.system.SystemAlerter._create_state_for_system")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_result_data_not_processed_bad_data_received(
            self, mock_ack, mock_create_state_for_system,
            mock_process_results) -> None:
        mock_ack.return_value = None
        try:
            self.test_system_alerter.rabbitmq.connect()
            blocking_channel = self.test_system_alerter.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.bad_output_routing_key)
            del self.data_received_initially_no_alert['result']['data']
            body = json.dumps(self.data_received_initially_no_alert)
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_create_state_for_system.assert_not_called()
            mock_process_results.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.system.SystemAlerter._process_errors")
    @mock.patch(
        "src.alerter.alerters.system.SystemAlerter._create_state_for_system")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_error_data_not_processed_bad_data_received(
            self, mock_ack, mock_create_state_for_system,
            mock_process_errors) -> None:

        mock_ack.return_value = None

        try:
            self.test_system_alerter.rabbitmq.connect()
            blocking_channel = self.test_system_alerter.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.bad_output_routing_key)
            del self.data_received_error_data['error']['meta_data']
            body = json.dumps(self.data_received_error_data)
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_create_state_for_system.assert_not_called()
            mock_process_errors.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch(
        "src.alerter.alerters.system.SystemAlerter._place_latest_data_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_place_latest_data_on_queue_not_called_bad_routing_key(
            self, mock_ack, mock_place_latest_data_on_queue) -> None:
        mock_ack.return_value = None
        try:
            self.test_system_alerter.rabbitmq.connect()
            blocking_channel = self.test_system_alerter.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.bad_output_routing_key)
            body = json.dumps(self.data_received_initially_no_alert)
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_place_latest_data_on_queue.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch(
        "src.alerter.alerters.system.SystemAlerter._place_latest_data_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_error_data_not_processed_bad_routing_key(
            self, mock_ack, mock_place_latest_data_on_queue) -> None:

        mock_ack.return_value = None
        try:
            self.test_system_alerter.rabbitmq.connect()
            blocking_channel = self.test_system_alerter.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.bad_output_routing_key)
            body = json.dumps(self.data_received_error_data)
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_place_latest_data_on_queue.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch(
        "src.alerter.alerters.system.SystemAlerter._place_latest_data_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_place_latest_data_on_queue_not_called_bad_data_received(
            self, mock_ack, mock_place_latest_data_on_queue) -> None:
        mock_ack.return_value = None
        try:
            self.test_system_alerter.rabbitmq.connect()
            blocking_channel = self.test_system_alerter.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.bad_output_routing_key)
            del self.data_received_initially_no_alert['result']['data']
            body = json.dumps(self.data_received_initially_no_alert)
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_place_latest_data_on_queue.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch(
        "src.alerter.alerters.system.SystemAlerter._place_latest_data_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_error_data_not_processed_bad_data_received(
            self, mock_ack, mock_place_latest_data_on_queue) -> None:
        mock_ack.return_value = None
        try:
            self.test_system_alerter.rabbitmq.connect()
            blocking_channel = self.test_system_alerter.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.bad_output_routing_key)
            del self.data_received_error_data['error']['meta_data']
            body = json.dumps(self.data_received_error_data)
            properties = pika.spec.BasicProperties()
            self.test_system_alerter._process_data(blocking_channel, method,
                                                   properties, body)
            mock_place_latest_data_on_queue.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))
