import json
import logging
import unittest
from datetime import datetime
from datetime import timedelta
from http.client import IncompleteRead
from unittest import mock

import pika
import pika.exceptions
from freezegun import freeze_time
from requests.exceptions import (ConnectionError as ReqConnectionError,
                                 ReadTimeout, ChunkedEncodingError)
from urllib3.exceptions import ProtocolError

from src.configs.repo import RepoConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.github import GitHubMonitor
from src.utils import env
from src.utils.constants import RAW_DATA_EXCHANGE, HEALTH_CHECK_EXCHANGE
from src.utils.exceptions import (PANICException, GitHubAPICallException,
                                  CannotAccessGitHubPageException,
                                  DataReadingException, JSONDecodeException,
                                  MessageWasNotDeliveredException)


class TestGitHubMonitor(unittest.TestCase):
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
        self.repo_id = 'test_repo_id'
        self.parent_id = 'test_parent_id'
        self.repo_name = 'test_repo'
        self.monitor_repo = True
        self.releases_page = 'test_url'
        self.routing_key = 'test_routing_key'
        self.test_data_str = 'test data'
        self.test_data_dict = {
            'test_key_1': 'test_val_1',
            'test_key_2': 'test_val_2',
        }
        self.test_timestamp = datetime(2012, 1, 1).timestamp()
        self.test_heartbeat = {
            'component_name': 'Test Component',
            'timestamp': self.test_timestamp,
        }
        self.test_queue_name = 'Test Queue'
        # In the real retrieved data there are more fields, but these are the
        # only ones that interest us so far.
        self.retrieved_metrics_example = [
            {'name': 'First Release 😮', 'tag_name': 'v1.0.0'},
            {'name': 'Release Candidate 1', 'tag_name': 'v0.1.0'},
        ]
        self.processed_data_example = {
            '0': {'release_name': 'First Release 😮', 'tag_name': 'v1.0.0'},
            '1': {'release_name': 'Release Candidate 1', 'tag_name': 'v0.1.0'},
        }
        self.test_exception = PANICException('test_exception', 1)
        self.repo_config = RepoConfig(self.repo_id, self.parent_id,
                                      self.repo_name, self.monitor_repo,
                                      self.releases_page)
        self.test_monitor = GitHubMonitor(self.monitor_name, self.repo_config,
                                          self.dummy_logger,
                                          self.monitoring_period, self.rabbitmq)

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        try:
            self.test_monitor.rabbitmq.connect()

            # Declare them before just in case there are tests which do not
            # use these queues and exchanges
            self.test_monitor.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.test_monitor.rabbitmq.exchange_declare(
                HEALTH_CHECK_EXCHANGE, 'topic', False, True, False, False)
            self.test_monitor.rabbitmq.exchange_declare(
                RAW_DATA_EXCHANGE, 'direct', False, True, False, False)

            self.test_monitor.rabbitmq.queue_purge(self.test_queue_name)
            self.test_monitor.rabbitmq.queue_delete(self.test_queue_name)
            self.test_monitor.rabbitmq.exchange_delete(RAW_DATA_EXCHANGE)
            self.test_monitor.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
            self.test_monitor.rabbitmq.disconnect()
        except Exception as e:
            print("Deletion of queues and exchanges failed: {}".format(e))

        self.dummy_logger = None
        self.rabbitmq = None
        self.test_exception = None
        self.repo_config = None
        self.test_monitor = None

    def test_str_returns_monitor_name(self) -> None:
        self.assertEqual(self.monitor_name, self.test_monitor.__str__())

    def test_get_monitor_period_returns_monitor_period(self) -> None:
        self.assertEqual(self.monitoring_period,
                         self.test_monitor.monitor_period)

    def test_get_monitor_name_returns_monitor_name(self) -> None:
        self.assertEqual(self.monitor_name, self.test_monitor.monitor_name)

    def test_repo_config_returns_repo_config(self) -> None:
        self.assertEqual(self.repo_config, self.test_monitor.repo_config)

    def test_initialise_rabbitmq_initializes_everything_as_expected(
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
            # to it. If this fails an exception is raised, hence the test fails.
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
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(GitHubMonitor, "_process_retrieved_data")
    @mock.patch.object(GitHubMonitor, "_process_error")
    def test_process_data_calls_process_error_on_retrieval_error(
            self, mock_process_error, mock_process_retrieved_data) -> None:
        # Do not test the processing of data for now
        mock_process_error.return_value = self.test_data_dict

        self.test_monitor._process_data(self.test_data_dict, True,
                                        self.test_exception)

        # Test passes if _process_error is called once and
        # process_retrieved_data is not called
        self.assertEqual(1, mock_process_error.call_count)
        self.assertEqual(0, mock_process_retrieved_data.call_count)

    @mock.patch.object(GitHubMonitor, "_process_retrieved_data")
    @mock.patch.object(GitHubMonitor, "_process_error")
    def test_process_data_calls_process_retrieved_data_on_retrieval_success(
            self, mock_process_error, mock_process_retrieved_data) -> None:
        # Do not test the processing of data for now
        mock_process_retrieved_data.return_value = self.test_data_dict

        self.test_monitor._process_data(self.test_data_dict, False, None)

        # Test passes if _process_error is called once and
        # process_retrieved_data is not called
        self.assertEqual(0, mock_process_error.call_count)
        self.assertEqual(1, mock_process_retrieved_data.call_count)

    def test_send_heartbeat_sends_a_heartbeat_correctly(self) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_heartbeat, and checks that the
        # heartbeat is received
        try:
            self.test_monitor._initialise_rabbitmq()

            # Delete the queue before to avoid messages in the queue on error.
            self.test_monitor.rabbitmq.queue_delete(self.test_queue_name)

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

            # Check that the message received is actually the HB
            _, _, body = self.test_monitor.rabbitmq.basic_get(
                self.test_queue_name)
            self.assertEqual(self.test_heartbeat, json.loads(body))
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    def test_display_data_returns_the_correct_string(self) -> None:
        expected_output = json.dumps(self.processed_data_example,
                                     ensure_ascii=False).encode('utf8').decode()
        actual_output = self.test_monitor._display_data(
            self.processed_data_example)
        self.assertEqual(expected_output, actual_output)

    @freeze_time("2012-01-01")
    def test_process_error_returns_expected_data(self) -> None:
        expected_output = {
            'error': {
                'meta_data': {
                    'monitor_name': self.test_monitor.monitor_name,
                    'repo_name': self.test_monitor.repo_config.repo_name,
                    'repo_id': self.test_monitor.repo_config.repo_id,
                    'repo_parent_id': self.test_monitor.repo_config.parent_id,
                    'time': self.test_timestamp
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
                    'repo_name': self.test_monitor.repo_config.repo_name,
                    'repo_id': self.test_monitor.repo_config.repo_id,
                    'repo_parent_id': self.test_monitor.repo_config.parent_id,
                    'time': self.test_timestamp
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

            # Delete the queue before to avoid messages in the queue on error.
            self.test_monitor.rabbitmq.queue_delete(self.test_queue_name)

            res = self.test_monitor.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_monitor.rabbitmq.queue_bind(
                queue=self.test_queue_name, exchange=RAW_DATA_EXCHANGE,
                routing_key='github')

            self.test_monitor._send_alerts(self.processed_data_example)

            # By re-declaring the queue again we can get the number of messages
            # in the queue.
            res = self.test_monitor.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            self.assertEqual(1, res.method.message_count)

            # Check that the message received is actually the processed data
            _, _, body = self.test_monitor.rabbitmq.basic_get(
                self.test_queue_name)
            self.assertEqual(self.processed_data_example, json.loads(body))
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch.object(GitHubMonitor, "_get_data")
    def test_monitor_sends_data_and_hb_if_data_retrieve_and_processing_success(
            self, mock_get_data) -> None:
        expected_output_data = {
            'result': {
                'meta_data': {
                    'monitor_name': self.test_monitor.monitor_name,
                    'repo_name': self.test_monitor.repo_config.repo_name,
                    'repo_id': self.test_monitor.repo_config.repo_id,
                    'repo_parent_id': self.test_monitor.repo_config.parent_id,
                    'time': self.test_timestamp
                },
                'data': self.processed_data_example,
            }
        }
        expected_output_hb = {
            'component_name': self.test_monitor.monitor_name,
            'timestamp': self.test_timestamp
        }

        try:
            mock_get_data.return_value = self.retrieved_metrics_example
            self.test_monitor._initialise_rabbitmq()

            # Delete the queue before to avoid messages in the queue on error.
            self.test_monitor.rabbitmq.queue_delete(self.test_queue_name)

            res = self.test_monitor.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_monitor.rabbitmq.queue_bind(
                queue=self.test_queue_name, exchange=RAW_DATA_EXCHANGE,
                routing_key='github')
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
            # There must be 2 messages in the queue, the heartbeat and the
            # processed data
            self.assertEqual(2, res.method.message_count)

            # Check that the message received is actually the processed data
            _, _, body = self.test_monitor.rabbitmq.basic_get(
                self.test_queue_name)
            self.assertEqual(expected_output_data, json.loads(body))

            # Check that the message received is actually the HB
            _, _, body = self.test_monitor.rabbitmq.basic_get(
                self.test_queue_name)
            self.assertEqual(expected_output_hb, json.loads(body))
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(GitHubMonitor, "_process_data")
    @mock.patch.object(GitHubMonitor, "_get_data")
    def test_monitor_sends_no_data_and_hb_if_data_ret_success_and_proc_fails(
            self, mock_get_data, mock_process_data) -> None:
        mock_process_data.side_effect = self.test_exception
        mock_get_data.return_value = self.retrieved_metrics_example
        try:
            self.test_monitor._initialise_rabbitmq()

            # Delete the queue before to avoid messages in the queue on error.
            self.test_monitor.rabbitmq.queue_delete(self.test_queue_name)

            res = self.test_monitor.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_monitor.rabbitmq.queue_bind(
                queue=self.test_queue_name, exchange=RAW_DATA_EXCHANGE,
                routing_key='github')
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
            # There must be 0 messages in the queue.
            self.assertEqual(0, res.method.message_count)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(GitHubMonitor, "_get_data")
    def test_monitor_sends_no_data_and_no_hb_on_get_data_unexpected_exception(
            self, mock_get_data) -> None:
        mock_get_data.side_effect = self.test_exception
        try:
            self.test_monitor._initialise_rabbitmq()

            # Delete the queue before to avoid messages in the queue on error.
            self.test_monitor.rabbitmq.queue_delete(self.test_queue_name)

            res = self.test_monitor.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_monitor.rabbitmq.queue_bind(
                queue=self.test_queue_name, exchange=RAW_DATA_EXCHANGE,
                routing_key='github')
            self.test_monitor.rabbitmq.queue_bind(
                queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
                routing_key='heartbeat.worker')

            self.assertRaises(PANICException, self.test_monitor._monitor)

            # By re-declaring the queue again we can get the number of messages
            # in the queue.
            res = self.test_monitor.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            # There must be 0 messages in the queue.
            self.assertEqual(0, res.method.message_count)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch.object(GitHubMonitor, "_get_data")
    def test_monitor_sends_gh_api_call_exception_data_and_hb_on_api_call_err(
            self, mock_get_data) -> None:
        api_call_err_return = {
            "message": "Not Found",
            "documentation_url":
                "https://docs.github.com/rest/reference/repos#list-releases"
        }
        mock_get_data.return_value = api_call_err_return
        data_ret_exception = GitHubAPICallException(
            api_call_err_return['message'])
        expected_output_data = {
            'error': {
                'meta_data': {
                    'monitor_name': self.test_monitor.monitor_name,
                    'repo_name': self.test_monitor.repo_config.repo_name,
                    'repo_id': self.test_monitor.repo_config.repo_id,
                    'repo_parent_id': self.test_monitor.repo_config.parent_id,
                    'time': self.test_timestamp
                },
                'message': data_ret_exception.message,
                'code': data_ret_exception.code,
            }
        }
        expected_output_hb = {
            'component_name': self.test_monitor.monitor_name,
            'timestamp': self.test_timestamp
        }
        try:
            self.test_monitor._initialise_rabbitmq()

            # Delete the queue before to avoid messages in the queue on error.
            self.test_monitor.rabbitmq.queue_delete(self.test_queue_name)

            res = self.test_monitor.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_monitor.rabbitmq.queue_bind(
                queue=self.test_queue_name, exchange=RAW_DATA_EXCHANGE,
                routing_key='github')
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
            # There must be 2 messages in the queue, the heartbeat and the
            # exception details.
            self.assertEqual(2, res.method.message_count)

            # Check that the message received is actually the processed data
            _, _, body = self.test_monitor.rabbitmq.basic_get(
                self.test_queue_name)
            self.assertEqual(expected_output_data, json.loads(body))

            # Check that the message received is actually the HB
            _, _, body = self.test_monitor.rabbitmq.basic_get(
                self.test_queue_name)
            self.assertEqual(expected_output_hb, json.loads(body))
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch.object(GitHubMonitor, "_get_data")
    def test_monitor_sends_exception_data_and_hb_on_expected_exceptions(
            self, mock_get_data) -> None:
        json_decode_error = json.JSONDecodeError(msg='test error', doc='test',
                                                 pos=2)
        errors_exceptions_dict = {
            ReqConnectionError('test'): CannotAccessGitHubPageException(
                self.repo_config.releases_page),
            ReadTimeout('test'): CannotAccessGitHubPageException(
                self.repo_config.releases_page),
            IncompleteRead('test'): DataReadingException(
                self.monitor_name, self.repo_config.releases_page),
            ChunkedEncodingError('test'): DataReadingException(
                self.monitor_name, self.repo_config.releases_page),
            ProtocolError('test'): DataReadingException(
                self.monitor_name, self.repo_config.releases_page),
            json_decode_error: JSONDecodeException(json_decode_error)
        }
        try:
            self.test_monitor._initialise_rabbitmq()
            for error, data_ret_exception in errors_exceptions_dict.items():
                mock_get_data.side_effect = error
                expected_output_data = {
                    'error': {
                        'meta_data': {
                            'monitor_name': self.test_monitor.monitor_name,
                            'repo_name':
                                self.test_monitor.repo_config.repo_name,
                            'repo_id': self.test_monitor.repo_config.repo_id,
                            'repo_parent_id':
                                self.test_monitor.repo_config.parent_id,
                            'time': self.test_timestamp
                        },
                        'message': data_ret_exception.message,
                        'code': data_ret_exception.code,
                    }
                }
                expected_output_hb = {
                    'component_name': self.test_monitor.monitor_name,
                    'timestamp': self.test_timestamp
                }
                # Delete the queue before to avoid messages in the queue on
                # error.
                self.test_monitor.rabbitmq.queue_delete(self.test_queue_name)

                res = self.test_monitor.rabbitmq.queue_declare(
                    queue=self.test_queue_name, durable=True, exclusive=False,
                    auto_delete=False, passive=False
                )
                self.assertEqual(0, res.method.message_count)
                self.test_monitor.rabbitmq.queue_bind(
                    queue=self.test_queue_name, exchange=RAW_DATA_EXCHANGE,
                    routing_key='github')
                self.test_monitor.rabbitmq.queue_bind(
                    queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
                    routing_key='heartbeat.worker')

                self.test_monitor._monitor()

                # By re-declaring the queue again we can get the number of
                # messages in the queue.
                res = self.test_monitor.rabbitmq.queue_declare(
                    queue=self.test_queue_name, durable=True, exclusive=False,
                    auto_delete=False, passive=True
                )
                # There must be 2 messages in the queue, the heartbeat and the
                # processed data
                self.assertEqual(2, res.method.message_count)

                # Check that the message received is actually the processed data
                _, _, body = self.test_monitor.rabbitmq.basic_get(
                    self.test_queue_name)
                self.assertEqual(expected_output_data, json.loads(body))

                # Check that the message received is actually the HB
                _, _, body = self.test_monitor.rabbitmq.basic_get(
                    self.test_queue_name)
                self.assertEqual(expected_output_hb, json.loads(body))
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(GitHubMonitor, "_get_data")
    def test_monitor_raises_msg_not_delivered_exception_if_data_not_routed(
            self, mock_get_data) -> None:
        mock_get_data.return_value = self.retrieved_metrics_example
        try:
            self.test_monitor._initialise_rabbitmq()

            self.assertRaises(MessageWasNotDeliveredException,
                              self.test_monitor._monitor)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch.object(GitHubMonitor, "_get_data")
    def test_monitor_raises_msg_not_del_except_if_hb_not_routed_and_sends_data(
            self, mock_get_data) -> None:
        mock_get_data.return_value = self.retrieved_metrics_example
        expected_output_data = {
            'result': {
                'meta_data': {
                    'monitor_name': self.test_monitor.monitor_name,
                    'repo_name': self.test_monitor.repo_config.repo_name,
                    'repo_id': self.test_monitor.repo_config.repo_id,
                    'repo_parent_id': self.test_monitor.repo_config.parent_id,
                    'time': self.test_timestamp
                },
                'data': self.processed_data_example,
            }
        }
        try:
            self.test_monitor._initialise_rabbitmq()

            self.test_monitor.rabbitmq.queue_delete(self.test_queue_name)

            res = self.test_monitor.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_monitor.rabbitmq.queue_bind(
                queue=self.test_queue_name, exchange=RAW_DATA_EXCHANGE,
                routing_key='github')

            self.assertRaises(MessageWasNotDeliveredException,
                              self.test_monitor._monitor)

            # By re-declaring the queue again we can get the number of
            # messages in the queue.
            res = self.test_monitor.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            # There must be 1 message in the queue, the processed data
            self.assertEqual(1, res.method.message_count)

            # Check that the message received is actually the processed data
            _, _, body = self.test_monitor.rabbitmq.basic_get(
                self.test_queue_name)
            self.assertEqual(expected_output_data, json.loads(body))
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(GitHubMonitor, "_send_data")
    @mock.patch.object(GitHubMonitor, "_get_data")
    def test_monitor_send_data_raises_amqp_channel_error_on_channel_error(
            self, mock_get_data, mock_send_data) -> None:
        mock_get_data.return_value = self.retrieved_metrics_example
        mock_send_data.side_effect = pika.exceptions.AMQPChannelError('test')
        try:
            self.test_monitor._initialise_rabbitmq()

            self.assertRaises(pika.exceptions.AMQPChannelError,
                              self.test_monitor._monitor)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch.object(GitHubMonitor, "_send_heartbeat")
    @mock.patch.object(GitHubMonitor, "_get_data")
    def test_monitor_send_hb_raises_amqp_chan_err_on_chan_err_and_sends_data(
            self, mock_get_data, mock_send_heartbeat) -> None:
        mock_get_data.return_value = self.retrieved_metrics_example
        mock_send_heartbeat.side_effect = \
            pika.exceptions.AMQPChannelError('test')
        expected_output_data = {
            'result': {
                'meta_data': {
                    'monitor_name': self.test_monitor.monitor_name,
                    'repo_name': self.test_monitor.repo_config.repo_name,
                    'repo_id': self.test_monitor.repo_config.repo_id,
                    'repo_parent_id': self.test_monitor.repo_config.parent_id,
                    'time': self.test_timestamp
                },
                'data': self.processed_data_example,
            }
        }
        try:
            self.test_monitor._initialise_rabbitmq()

            self.test_monitor.rabbitmq.queue_delete(self.test_queue_name)

            res = self.test_monitor.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_monitor.rabbitmq.queue_bind(
                queue=self.test_queue_name, exchange=RAW_DATA_EXCHANGE,
                routing_key='github')
            self.test_monitor.rabbitmq.queue_bind(
                queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
                routing_key='heartbeat.worker')

            self.assertRaises(pika.exceptions.AMQPChannelError,
                              self.test_monitor._monitor)

            # By re-declaring the queue again we can get the number of
            # messages in the queue.
            res = self.test_monitor.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            # There must be 1 message in the queue, the processed data
            self.assertEqual(1, res.method.message_count)

            # Check that the message received is actually the processed data
            _, _, body = self.test_monitor.rabbitmq.basic_get(
                self.test_queue_name)
            self.assertEqual(expected_output_data, json.loads(body))
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(GitHubMonitor, "_send_data")
    @mock.patch.object(GitHubMonitor, "_get_data")
    def test_monitor_send_data_raises_amqp_conn_error_on_conn_error(
            self, mock_get_data, mock_send_data) -> None:
        mock_get_data.return_value = self.retrieved_metrics_example
        mock_send_data.side_effect = pika.exceptions.AMQPConnectionError('test')
        try:
            self.test_monitor._initialise_rabbitmq()

            self.assertRaises(pika.exceptions.AMQPConnectionError,
                              self.test_monitor._monitor)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch.object(GitHubMonitor, "_send_heartbeat")
    @mock.patch.object(GitHubMonitor, "_get_data")
    def test_monitor_send_hb_raises_amqp_conn_err_on_conn_err_and_sends_data(
            self, mock_get_data, mock_send_heartbeat) -> None:
        mock_get_data.return_value = self.retrieved_metrics_example
        mock_send_heartbeat.side_effect = \
            pika.exceptions.AMQPConnectionError('test')
        expected_output_data = {
            'result': {
                'meta_data': {
                    'monitor_name': self.test_monitor.monitor_name,
                    'repo_name': self.test_monitor.repo_config.repo_name,
                    'repo_id': self.test_monitor.repo_config.repo_id,
                    'repo_parent_id': self.test_monitor.repo_config.parent_id,
                    'time': self.test_timestamp
                },
                'data': self.processed_data_example,
            }
        }
        try:
            self.test_monitor._initialise_rabbitmq()

            self.test_monitor.rabbitmq.queue_delete(self.test_queue_name)

            res = self.test_monitor.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_monitor.rabbitmq.queue_bind(
                queue=self.test_queue_name, exchange=RAW_DATA_EXCHANGE,
                routing_key='github')
            self.test_monitor.rabbitmq.queue_bind(
                queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
                routing_key='heartbeat.worker')

            self.assertRaises(pika.exceptions.AMQPConnectionError,
                              self.test_monitor._monitor)

            # By re-declaring the queue again we can get the number of
            # messages in the queue.
            res = self.test_monitor.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            # There must be 1 message in the queue, the processed data
            self.assertEqual(1, res.method.message_count)

            # Check that the message received is actually the processed data
            _, _, body = self.test_monitor.rabbitmq.basic_get(
                self.test_queue_name)
            self.assertEqual(expected_output_data, json.loads(body))
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(GitHubMonitor, "_send_data")
    @mock.patch.object(GitHubMonitor, "_get_data")
    def test_monitor_does_not_send_hb_and_data_if_send_data_fails(
            self, mock_get_data, mock_send_data) -> None:
        mock_get_data.return_value = self.retrieved_metrics_example
        exception_types_dict = \
            {
                Exception('test'): Exception,
                pika.exceptions.AMQPConnectionError('test'):
                    pika.exceptions.AMQPConnectionError,
                pika.exceptions.AMQPChannelError('test'):
                    pika.exceptions.AMQPChannelError,
                MessageWasNotDeliveredException('test'):
                    MessageWasNotDeliveredException
            }
        try:
            self.test_monitor._initialise_rabbitmq()
            for exception, exception_type in exception_types_dict.items():
                mock_send_data.side_effect = exception
                self.test_monitor.rabbitmq.queue_delete(
                    self.test_queue_name)

                res = self.test_monitor.rabbitmq.queue_declare(
                    queue=self.test_queue_name, durable=True, exclusive=False,
                    auto_delete=False, passive=False
                )
                self.assertEqual(0, res.method.message_count)
                self.test_monitor.rabbitmq.queue_bind(
                    queue=self.test_queue_name,
                    exchange=HEALTH_CHECK_EXCHANGE,
                    routing_key='heartbeat.worker')
                self.test_monitor.rabbitmq.queue_bind(
                    queue=self.test_queue_name, exchange=RAW_DATA_EXCHANGE,
                    routing_key='github')

                self.assertRaises(exception_type, self.test_monitor._monitor)

                # By re-declaring the queue again we can get the number of
                # messages in the queue.
                res = self.test_monitor.rabbitmq.queue_declare(
                    queue=self.test_queue_name, durable=True,
                    exclusive=False, auto_delete=False, passive=True
                )
                # There must be no messages in the queue.
                self.assertEqual(0, res.method.message_count)
        except Exception as e:
            self.fail("Test failed: {}".format(e))
