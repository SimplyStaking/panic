import logging
import unittest
from datetime import datetime
from datetime import timedelta

from src.configs.system import SystemConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.system import SystemMonitor
from src.utils import env
from src.utils.exceptions import (PANICException)


class TestChainlinkNodeMonitor(unittest.TestCase):
    def setUp(self) -> None:
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbit_ip = env.RABBIT_IP
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)
        self.monitor_name = 'test_monitor'
        self.monitoring_period = 10
        self.node_id = 'test_node_id'
        self.parent_id = 'test_parent_id'
        self.node_name = 'test_node'
        self.monitor_node = True
        self.node_prometheus_urls = ['test_url_1', 'test_url_2', 'test_url_3']
        self.routing_key = 'test_routing_key'
        self.test_data_str = 'test data'
        self.test_data_dict = {
            'test_key_1': 'test_val_1',
            'test_key_2': 'test_val_2',
        }
        self.test_heartbeat = {
            'component_name': 'Test Component',
            'is_alive': True,
            'timestamp': datetime(2012, 1, 1).timestamp(),
        }
        self.test_queue_name = 'Test Queue'
        # self.metrics_to_monitor = ['head_tracker_current_head',
        #                            'head_tracker_heads_in_queue',
        #                            'head_tracker_heads_received_total',
        #                            'head_tracker_num_heads_dropped_total',
        #                            'job_subscriber_subscriptions',
        #                            'max_unconfirmed_blocks',
        #                            'process_start_time_seconds',
        #                            'tx_manager_num_gas_bumps_total',
        #                            'tx_manager_gas_bump_exceeds_limit_total',
        #                            'unconfirmed_transactions',
        #                            'run_status_update_total',
        #                            ]
        # self.retrieved_metrics_example = {
        #     'head_tracker_current_head',
        #     'head_tracker_heads_in_queue',
        #     'head_tracker_heads_received_total',
        #     'head_tracker_num_heads_dropped_total',
        #     'job_subscriber_subscriptions',
        #     'max_unconfirmed_blocks',
        #     'process_start_time_seconds',
        #     'tx_manager_num_gas_bumps_total',
        #     'tx_manager_gas_bump_exceeds_limit_total',
        #     'unconfirmed_transactions',
        #     'run_status_update_total': {
        #         '{"cpu": "0", "mode": "idle"}': 3626110.54,
        #         '{"cpu": "0", "mode": "iowait"}': 16892.07,
        #         '{"cpu": "0", "mode": "irq"}': 0.0,
        #         '{"cpu": "0", "mode": "nice"}': 131.77,
        #         '{"cpu": "0", "mode": "softirq"}': 8165.66,
        #         '{"cpu": "0", "mode": "steal"}': 0.0,
        #         '{"cpu": "0", "mode": "system"}': 46168.15,
        #         '{"cpu": "0", "mode": "user"}': 238864.68,
        #         '{"cpu": "1", "mode": "idle"}': 3630087.24,
        #         '{"cpu": "1", "mode": "iowait"}': 17084.42,
        #         '{"cpu": "1", "mode": "irq"}': 0.0,
        #         '{"cpu": "1", "mode": "nice"}': 145.18,
        #         '{"cpu": "1", "mode": "softirq"}': 5126.93,
        #         '{"cpu": "1", "mode": "steal"}': 0.0,
        #         '{"cpu": "1", "mode": "system"}': 46121.4,
        #         '{"cpu": "1", "mode": "user"}': 239419.51},
        # }
        # self.processed_data_example = {
        #     'process_cpu_seconds_total': 2786.82,
        #     'process_memory_usage': 0.0,
        #     'virtual_memory_usage': 118513664.0,
        #     'open_file_descriptors': 0.78125,
        #     'system_cpu_usage': 7.85,
        #     'system_ram_usage': 34.09,
        #     'system_storage_usage': 44.37,
        #     'network_transmit_bytes_total': 1011572205557.0,
        #     'network_receive_bytes_total': 722359147027.0,
        #     'disk_io_time_seconds_total': 76647.0,
        # }
        # self.test_exception = PANICException('test_exception', 1)
        # self.system_config = SystemConfig(self.system_id, self.parent_id,
        #                                   self.system_name, self.monitor_system,
        #                                   self.node_exporter_url)
        # self.test_monitor = SystemMonitor(self.monitor_name, self.system_config,
        #                                   self.dummy_logger,
        #                                   self.monitoring_period, self.rabbitmq)
