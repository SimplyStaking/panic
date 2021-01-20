import logging
import unittest
from datetime import datetime
from datetime import timedelta
from unittest import mock

import pika
from freezegun import freeze_time

from src.configs.system import SystemConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.system import SystemMonitor
from src.utils.constants import RAW_DATA_EXCHANGE, HEALTH_CHECK_EXCHANGE
from src.utils.exceptions import PANICException


class TestSystemMonitor(unittest.TestCase):
    def setUp(self) -> None:
        self.dummy_logger = logging.getLogger('Dummy')
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger,
            connection_check_time_interval=self.connection_check_time_interval)
        self.monitor_name = 'test_monitor'
        self.monitoring_period = 10
        self.system_id = 'test_system_id'
        self.parent_id = 'test_parent_id'
        self.system_name = 'test_system'
        self.monitor_system = True
        self.node_exporter_url = 'test_url'
        self.routing_key = 'test_routing_key'
        self.test_data_str = 'test data'
        self.test_data_dict = {
            'test_key_1': 'test_val_1',
            'test_key_2': 'test_val_2',
        }
        self.test_heartbeat = {
            'component_name': 'Test Component',
            'timestamp': datetime.now().timestamp()
        }
        self.test_queue_name = 'Test Queue'
        self.metrics_to_monitor = [
            'process_cpu_seconds_total', 'go_memstats_alloc_bytes',
            'go_memstats_alloc_bytes_total', 'process_virtual_memory_bytes',
            'process_max_fds', 'process_open_fds', 'node_cpu_seconds_total',
            'node_filesystem_avail_bytes', 'node_filesystem_size_bytes',
            'node_memory_MemTotal_bytes', 'node_memory_MemAvailable_bytes',
            'node_network_transmit_bytes_total',
            'node_network_receive_bytes_total',
            'node_disk_io_time_seconds_total']
        self.retrieved_metrics_example = {
            'go_memstats_alloc_bytes': 2003024.0,
            'go_memstats_alloc_bytes_total': 435777412600.0,
            'node_cpu_seconds_total': {
                '{"cpu": "0", "mode": "idle"}': 3626110.54,
                '{"cpu": "0", "mode": "iowait"}': 16892.07,
                '{"cpu": "0", "mode": "irq"}': 0.0,
                '{"cpu": "0", "mode": "nice"}': 131.77,
                '{"cpu": "0", "mode": "softirq"}': 8165.66,
                '{"cpu": "0", "mode": "steal"}': 0.0,
                '{"cpu": "0", "mode": "system"}': 46168.15,
                '{"cpu": "0", "mode": "user"}': 238864.68,
                '{"cpu": "1", "mode": "idle"}': 3630087.24,
                '{"cpu": "1", "mode": "iowait"}': 17084.42,
                '{"cpu": "1", "mode": "irq"}': 0.0,
                '{"cpu": "1", "mode": "nice"}': 145.18,
                '{"cpu": "1", "mode": "softirq"}': 5126.93,
                '{"cpu": "1", "mode": "steal"}': 0.0,
                '{"cpu": "1", "mode": "system"}': 46121.4,
                '{"cpu": "1", "mode": "user"}': 239419.51},
            'node_disk_io_time_seconds_total': {
                '{"device": "dm-0"}': 38359.0,
                '{"device": "sda"}': 38288.0,
                '{"device": "sr0"}': 0.0},
            'node_filesystem_avail_bytes': {
                '{"device": "/dev/mapper/ubuntu--vg-ubuntu--lv", '
                '"fstype": "ext4", "mountpoint": "/"}': 57908170752.0,
                '{"device": "/dev/sda2", "fstype": "ext4", '
                '"mountpoint": "/boot"}': 729411584.0,
                '{"device": "lxcfs", "fstype": "fuse.lxcfs", '
                '"mountpoint": "/var/lib/lxcfs"}': 0.0,
                '{"device": "tmpfs", "fstype": "tmpfs", '
                '"mountpoint": "/run"}': 207900672.0,
                '{"device": "tmpfs", "fstype": "tmpfs", "mountpoint": '
                '"/run/lock"}': 5242880.0},
            'node_filesystem_size_bytes': {
                '{"device": "/dev/mapper/ubuntu--vg-ubuntu--lv", "fstype": '
                '"ext4", "mountpoint": "/"}': 104560844800.0,
                '{"device": "/dev/sda2", "fstype": "ext4", "mountpoint": '
                '"/boot"}': 1023303680.0,
                '{"device": "lxcfs", "fstype": "fuse.lxcfs", "mountpoint": '
                '"/var/lib/lxcfs"}': 0.0,
                '{"device": "tmpfs", "fstype": "tmpfs", "mountpoint": "/run"}':
                    209027072.0,
                '{"device": "tmpfs", "fstype": "tmpfs", "mountpoint": '
                '"/run/lock"}': 5242880.0},
            'node_memory_MemAvailable_bytes': 1377767424.0,
            'node_memory_MemTotal_bytes': 2090237952.0,
            'node_network_receive_bytes_total': {
                '{"device": "ens160"}': 722358765622.0,
                '{"device": "lo"}': 381405.0},
            'node_network_transmit_bytes_total': {
                '{"device": "ens160"}': 1011571824152.0,
                '{"device": "lo"}': 381405.0},
            'process_cpu_seconds_total': 2786.82,
            'process_max_fds': 1024.0,
            'process_open_fds': 8.0,
            'process_virtual_memory_bytes': 118513664.0}
        self.processed_data_example = {
            'process_cpu_seconds_total': 2786.82,
            'process_memory_usage': 0.0,
            'virtual_memory_usage': 118513664.0,
            'open_file_descriptors': 0.78125,
            'system_cpu_usage': 7.85,
            'system_ram_usage': 34.09,
            'system_storage_usage': 44.37,
            'network_transmit_bytes_total': 1011572205557.0,
            'network_receive_bytes_total': 722359147027.0,
            'disk_io_time_seconds_total': 76647.0,
        }
        self.test_exception = PANICException('test_exception', 1)
        self.system_config = SystemConfig(self.system_id, self.parent_id,
                                          self.system_name, self.monitor_system,
                                          self.node_exporter_url)
        self.test_monitor = SystemMonitor(self.monitor_name, self.system_config,
                                          self.dummy_logger,
                                          self.monitoring_period, self.rabbitmq)

    def tearDown(self) -> None:
        self.dummy_logger = None
        self.rabbitmq = None
        self.test_exception = None
        self.system_config = None
        self.test_monitor = None

    def test_str_returns_monitor_name(self) -> None:
        self.assertEqual(self.monitor_name, self.test_monitor.__str__())

    def test_get_monitor_period_returns_monitor_period(self) -> None:
        self.assertEqual(self.monitoring_period,
                         self.test_monitor.monitor_period)

    def test_get_monitor_name_returns_monitor_name(self) -> None:
        self.assertEqual(self.monitor_name, self.test_monitor.monitor_name)

    def test_system_config_returns_system_config(self) -> None:
        self.assertEqual(self.system_config, self.test_monitor.system_config)

    def test_metrics_to_monitor_returns_metrics_to_monitor(self) -> None:
        self.assertEqual(self.metrics_to_monitor,
                         self.test_monitor.metrics_to_monitor)

    def test_initialize_rabbitmq_initializes_everything_as_expected(
            self) -> None:
        try:
            # To make sure that there is no connection/channel already
            # established
            self.assertIsNone(self.rabbitmq.connection)
            self.assertIsNone(self.rabbitmq.channel)

            # To make sure that the exchanges have not already been declared
            self.rabbitmq.connect()
            self.rabbitmq.exchange_delete(RAW_DATA_EXCHANGE)
            self.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
            self.rabbitmq.disconnect()

            self.test_monitor._initialise_rabbitmq()

            # Perform checks that the connection has been opened, marked as open
            # and that the delivery confirmation variable is set.
            self.assertTrue(self.test_monitor.rabbitmq.is_connected)
            self.assertTrue(self.test_monitor.rabbitmq.connection.is_open)
            self.assertTrue(
                self.test_monitor.rabbitmq.channel._delivery_confirmation)

            # Check whether the exchange has been creating by sending messages
            # to it. If this fails an exception is raised hence the test fails.
            self.test_monitor.rabbitmq.basic_publish_confirm(
                exchange=RAW_DATA_EXCHANGE, routing_key=self.routing_key,
                body=self.test_data_str, is_body_dict=False,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=False)
            self.test_monitor.rabbitmq.basic_publish_confirm(
                exchange=HEALTH_CHECK_EXCHANGE, routing_key=self.routing_key,
                body=self.test_data_str, is_body_dict=False,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=False)

            self.test_monitor.rabbitmq.exchange_delete(RAW_DATA_EXCHANGE)
            self.test_monitor.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
            self.test_monitor.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(SystemMonitor, "_process_retrieved_data")
    @mock.patch.object(SystemMonitor, "_process_error")
    def test_process_data_calls_process_error_retrieval_error(
            self, mock_process_error, mock_process_retrieved_data) -> None:
        # Do not test the processing of data for now
        mock_process_error.return_value = self.test_data_dict

        self.test_monitor._process_data(self.test_data_dict, True,
                                        self.test_exception)

        # Test passes if _process_error is called once and
        # process_retrieved_data is not called
        try:
            self.assertEqual(1, mock_process_error.call_count)
            self.assertEqual(0, mock_process_retrieved_data.call_count)
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(SystemMonitor, "_process_retrieved_data")
    @mock.patch.object(SystemMonitor, "_process_error")
    def test_process_data_calls_process_retrieved_data_on_retrieval_success(
            self, mock_process_error, mock_process_retrieved_data) -> None:
        # Do not test the processing of data for now
        mock_process_retrieved_data.return_value = self.test_data_dict

        self.test_monitor._process_data(self.test_data_dict, False, None)

        # Test passes if _process_error is called once and
        # process_retrieved_data is not called
        try:
            self.assertEqual(0, mock_process_error.call_count)
            self.assertEqual(1, mock_process_retrieved_data.call_count)
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    def test_send_heartbeat_sends_a_heartbeat_correctly(self) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_heartbeat, and checks that the
        # heartbeat is received
        try:
            self.test_monitor._initialise_rabbitmq()

            res = self.test_monitor.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_monitor.rabbitmq.queue_bind(
                queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
                routing_key='heartbeat.worker')
            self.test_monitor._send_heartbeat(self.test_heartbeat)

            # By re-declaring the queue again we can get the number of messages
            # in the queue.
            res = self.test_monitor.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            self.assertEqual(1, res.method.message_count)

            # Clean before test finishes
            self.test_monitor.rabbitmq.queue_delete(self.test_queue_name)
            self.test_monitor.rabbitmq.exchange_delete(RAW_DATA_EXCHANGE)
            self.test_monitor.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
            self.test_monitor.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    def test_display_data_returns_the_correct_string(self) -> None:
        expected_output = \
            "process_cpu_seconds_total={}, process_memory_usage={}, " \
            "virtual_memory_usage={}, open_file_descriptors={}, " \
            "system_cpu_usage={}, system_ram_usage={}, " \
            "system_storage_usage={}, network_transmit_bytes_total={}, " \
            "network_receive_bytes_total={}, disk_io_time_seconds_total={}" \
            "".format(self.processed_data_example['process_cpu_seconds_total'],
                      self.processed_data_example['process_memory_usage'],
                      self.processed_data_example['virtual_memory_usage'],
                      self.processed_data_example['open_file_descriptors'],
                      self.processed_data_example['system_cpu_usage'],
                      self.processed_data_example['system_ram_usage'],
                      self.processed_data_example['system_storage_usage'],
                      self.processed_data_example[
                          'network_transmit_bytes_total'],
                      self.processed_data_example[
                          'network_receive_bytes_total'],
                      self.processed_data_example['disk_io_time_seconds_total'])

        actual_output = self.test_monitor._display_data(
            self.processed_data_example)
        self.assertEqual(expected_output, actual_output)

    @freeze_time("2012-01-01")
    def test_process_error_returns_expected_data(self) -> None:
        expected_output = {
            'error': {
                'meta_data': {
                    'monitor_name': self.test_monitor.monitor_name,
                    'system_name': self.test_monitor.system_config.system_name,
                    'system_id': self.test_monitor.system_config.system_id,
                    'system_parent_id':
                        self.test_monitor.system_config.parent_id,
                    'time': datetime(2012, 1, 1).timestamp()
                },
                'message': self.test_exception.message,
                'code': self.test_exception.code,
            }
        }

        actual_output = self.test_monitor._process_error(self.test_exception)
        self.assertEqual(actual_output, expected_output)

    @freeze_time("2012-01-01")
    def test_process_retrieved_data_returns_expected_data(self) -> None:
        expected_output = {
            'result': {
                'meta_data': {
                    'monitor_name': self.test_monitor.monitor_name,
                    'system_name': self.test_monitor.system_config.system_name,
                    'system_id': self.test_monitor.system_config.system_id,
                    'system_parent_id':
                        self.test_monitor.system_config.parent_id,
                    'time': datetime(2012, 1, 1).timestamp()
                },
                'data': self.processed_data_example,
            }
        }

        actual_output = self.test_monitor._process_retrieved_data(
            self.retrieved_metrics_example)
        self.assertEqual(expected_output, actual_output)

    def test_send_data_sends_data_correctly(self) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_data, and checks that the
        # data is received
        try:
            self.test_monitor._initialise_rabbitmq()

            res = self.test_monitor.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_monitor.rabbitmq.queue_bind(
                queue=self.test_queue_name, exchange=RAW_DATA_EXCHANGE,
                routing_key='system')
            self.test_monitor._send_data(self.processed_data_example)

            # By re-declaring the queue again we can get the number of messages
            # in the queue.
            res = self.test_monitor.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            self.assertEqual(1, res.method.message_count)

            # Clean before test finishes
            self.test_monitor.rabbitmq.queue_delete(self.test_queue_name)
            self.test_monitor.rabbitmq.exchange_delete(RAW_DATA_EXCHANGE)
            self.test_monitor.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
            self.test_monitor.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(SystemMonitor, "_get_data")
    def test_monitor_sends_data_and_hb_if_data_retrieve_and_processing_success(
            self, mock_get_data) -> None:
        mock_get_data.return_value = self.retrieved_metrics_example
        self.test_monitor._initialise_rabbitmq()

        res = self.test_monitor.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=False
        )
        self.assertEqual(0, res.method.message_count)
        self.test_monitor.rabbitmq.queue_bind(
            queue=self.test_queue_name, exchange=RAW_DATA_EXCHANGE,
            routing_key='system')
        self.test_monitor.rabbitmq.queue_bind(
            queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
            routing_key='heartbeat.worker')

        self.test_monitor._monitor()

        # By re-declaring the queue again we can get the number of messages
        # in the queue.
        res = self.test_monitor.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=True
        )
        # There must be 2 messages in the queue, the heartbeat and the processed
        # data
        self.assertEqual(2, res.method.message_count)

        # Clean before test finishes
        self.test_monitor.rabbitmq.queue_delete(self.test_queue_name)
        self.test_monitor.rabbitmq.exchange_delete(RAW_DATA_EXCHANGE)
        self.test_monitor.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
        self.test_monitor.rabbitmq.disconnect()

    # TODO: After initialize data always delete queues and exchanges
    # TODO: Check whether queue data can be obtained so that we can compare the
    #     : sent messages.

    def test_monitor_sends_no_data_and_hb_if_data_ret_success_and_proc_fails(
            self) -> None:
        pass

    def test_monitor_sends_system_is_down_data_and_hb_on_req_connection_error(
            self) -> None:
        # TODO: Need to Mock get_data to raise an exception
        pass

    def test_monitor_sends_system_is_down_data_and_hb_on_read_timeout_error(
            self) -> None:
        pass

    def test_monitor_sends_data_reading_exception_data_and_hb_on_incomplete_read_error(
            self) -> None:
        pass

    def test_monitor_sends_data_reading_except_data_and_hb_on_chunked_encoding_error(
            self) -> None:
        pass

    def test_monitor_sends_data_reading_exception_data_and_hb_on_protocol_error(
            self) -> None:
        pass

    def test_monitor_sends_invalid_url_exception_data_and_hb_on_invalid_url_error(
            self) -> None:
        pass

    def test_monitor_sends_invalid_url_exception_data_and_hb_on_invalid_schema_error(
            self) -> None:
        pass

    def test_monitor_sends_invalid_url_exception_data_and_hb_on_missing_schema_error(
            self) -> None:
        pass

    def test_monitor_sends_metric_not_found_data_and_hb_on_metric_not_found_error(
            self) -> None:
        pass

    def test_monitor_sends_no_data_and_no_hb_on_get_data_unexpected_exception(
            self) -> None:
        pass

    def test_monitor_raises_message_not_delivered_exception_if_data_not_routed(self) -> None:
        pass

    def test_monitor_raises_message_not_delivered_exception_if_hb_not_routed(self) -> None:
        pass

    def test_monitor_send_data_raises_amqp_channel_error_on_channel_error(self) -> None:
        pass

    def test_monitor_send_hb_raises_amqp_channel_error_on_channel_error(
            self) -> None:
        pass

    def test_monitor_send_data_raises_amqp_conn_error_on_conn_error(self) -> None:
        pass

    def test_monitor_send_hb_raises_amqp_conn_error_on_conn_error(
            self) -> None:
        pass

    def test_monitor_does_not_send_hb_if_send_data_fails(self) -> None:
        pass

    # TODO: In the monitor's _monitor() function we can test different scenarios
    #     : by checking that certain exceptions are called.
    # TODO: Remove tearDown() commented code
    # TODO: Remove SIGHUP comment
    # TODO: Fix rabbit host
