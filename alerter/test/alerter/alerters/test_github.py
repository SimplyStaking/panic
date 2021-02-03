import logging
import unittest
import pika
import json
import datetime
from queue import Queue
from unittest import mock

from src.alerter.alerts.github_alerts import NewGitHubReleaseAlert
from src.message_broker.rabbitmq import RabbitMQApi
from src.alerter.alerters.github import GithubAlerter
from src.utils.env import ALERTER_PUBLISHING_QUEUE_SIZE, RABBIT_IP
from src.utils.constants import (ALERT_EXCHANGE, GITHUB_ALERTER_INPUT_QUEUE,
                                 GITHUB_ALERTER_INPUT_ROUTING_KEY,
                                 HEALTH_CHECK_EXCHANGE)


class TestGithubAlerter(unittest.TestCase):
    def setUp(self) -> None:
        self.dummy_logger = logging.getLogger('Dummy')
        self.connection_check_time_interval = datetime.timedelta(seconds=0)
        self.alert_input_exchange = ALERT_EXCHANGE

        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, RABBIT_IP,
            connection_check_time_interval=self.connection_check_time_interval)

        self.alerter_name = 'test_github_alerter'
        self.repo_name = 'simplyvc/panic/'
        self.repo_id = 'test_repo_id'
        self.parent_id = 'test_parent_id'
        self.github_name = 'test_github'
        self.last_monitored = 1611619200
        self.publishing_queue = Queue(ALERTER_PUBLISHING_QUEUE_SIZE)
        self.target_queue_used = "alert_router_queue"
        self.test_queue_name = 'test_alerter_queue'
        self.test_routing_key = 'test_alert_router.github'
        self.alert_router_routing_key = 'alert_router.system'
        self.test_github_alerter = GithubAlerter(
            self.alerter_name, self.dummy_logger
        )

        self.warning = "WARNING"
        self.info = "INFO"
        self.critical = "CRITICAL"
        self.error = "ERROR"
        self.none = None

        self.heartbeat_test = {
            'component_name': self.alerter_name,
            'timestamp': datetime.datetime(2021, 1, 28).timestamp()
        }
        self.heartbeat_queue = 'heartbeat queue'

        """
        ################# Metrics Received from Data Transformer ############
        """
        self.github_data_received = {
            "result": {
                "meta_data": {
                    "repo_name": self.repo_name,
                    "repo_id": self.repo_id,
                    "repo_parent_id": self.parent_id,
                    "last_monitored": self.last_monitored
                },
                "data": {
                    "no_of_releases": {
                        "current": 5,
                        "previous": 4,
                    },
                    "releases": {
                        "0": {
                            "release_name": "PANIC v2.0.2",
                            "tag_name": "2.0.2"
                        },
                        "1": {
                            "release_name": "PANIC v2.0.1",
                            "tag_name": "2.0.1"
                        },
                        "2": {
                            "release_name": "PANIC v2.0.0",
                            "tag_name": "2.0.0"
                        },
                        "3": {
                            "release_name": "PANIC v1.0.1",
                            "tag_name": "1.0.1"
                        },
                        "4": {
                            "release_name": "PANIC v1.0.0",
                            "tag_name": "1.0.0"
                        }
                    }
                }
            }
        }
        self.github_json = json.dumps(self.github_data_received).encode('utf-8')

        self.github_data_error = {
            "error": {
                "meta_data": {
                    "repo_name": self.repo_name,
                    "repo_id": self.repo_id,
                    "repo_parent_id": self.parent_id,
                    "time": self.last_monitored
                },
                "code": "5006",
            }
        }

        # Alert used for rabbitMQ testing
        self.alert = NewGitHubReleaseAlert(
            self.repo_name, "PANIC RELEASE","PANIC_TAG", self.info,
            self.last_monitored, self.parent_id,
            self.repo_id
        )

    def tearDown(self) -> None:
        self.dummy_logger = None
        self.rabbitmq = None
        self.publishing_queue = None
        self.test_github_alerter = None
        self.github_data_received = None

    def test_returns_alerter_name_as_str(self) -> None:
        self.assertEqual(self.alerter_name, self.test_github_alerter.__str__())

    def test_returns_alerter_name(self) -> None:
        self.assertEqual(self.alerter_name,
                         self.test_github_alerter.alerter_name)

    def test_returns_logger(self) -> None:
        self.assertEqual(self.dummy_logger, self.test_github_alerter.logger)

    def test_returns_publishing_queue_size(self) -> None:
        self.assertEqual(self.publishing_queue.qsize(),
                         self.test_github_alerter.publishing_queue.qsize())


    """
    ###################### Tests using RabbitMQ #######################
    """

    def test_initialise_rabbit_initialises_queues(self) -> None:
        self.test_github_alerter._initialise_rabbitmq()
        try:
            self.rabbitmq.connect_till_successful()
            self.rabbitmq.queue_declare(GITHUB_ALERTER_INPUT_QUEUE, passive=True)
        except pika.exceptions.ConnectionClosedByBroker:
            self.fail("Queue {} was not declared".format(GITHUB_ALERTER_INPUT_QUEUE))

    def test_initialise_rabbit_initialises_exchanges(self) -> None:
        self.test_github_alerter._initialise_rabbitmq()

        try:
            self.rabbitmq.connect_till_successful()
            self.rabbitmq.exchange_declare(ALERT_EXCHANGE, passive=True)
        except pika.exceptions.ConnectionClosedByBroker:
            self.fail("Exchange {} was not declared".format(ALERT_EXCHANGE))

    def test_send_alert_correctly(
            self) -> None:
        try:
            self.test_github_alerter._initialise_rabbitmq()
            self.test_github_alerter.rabbitmq.queue_delete(self.target_queue_used)

            res = self.test_github_alerter.rabbitmq.queue_declare(
                queue=self.target_queue_used, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_github_alerter.rabbitmq.queue_bind(
                queue=self.target_queue_used, exchange=ALERT_EXCHANGE,
                routing_key=self.alert_router_routing_key)

            self.test_github_alerter.rabbitmq.basic_publish_confirm(
                exchange=ALERT_EXCHANGE, routing_key=self.alert_router_routing_key,
                body=self.alert.alert_data, is_body_dict=True,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=True)

            res = self.test_github_alerter.rabbitmq.queue_declare(
                queue=self.target_queue_used, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            self.assertEqual(1, res.method.message_count)

            _, _, body = self.test_github_alerter.rabbitmq.basic_get(
                self.target_queue_used)
            # For some reason during the conversion [] are swapped to ()
            self.assertEqual(json.loads(json.dumps(self.alert.alert_data)), json.loads(body))

            self.test_github_alerter.rabbitmq.queue_purge(self.target_queue_used)
            self.test_github_alerter.rabbitmq.queue_delete(self.target_queue_used)
            self.test_github_alerter.rabbitmq.exchange_delete(ALERT_EXCHANGE)
            self.test_github_alerter.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.alerter.RabbitMQApi.basic_publish_confirm", autospec=True)
    @mock.patch("src.alerter.alerters.alerter.RabbitMQApi.basic_ack", autospec=True)
    @mock.patch("src.alerter.alerters.github.NewGitHubReleaseAlert", autospec=True)
    def test_new_github_release_alert(
            self, mock_new_github_release, mock_ack, mock_basic_publish_confirm):
        self.rabbitmq.connect_till_successful()
        self.rabbitmq.exchange_declare(ALERT_EXCHANGE, "topic", False, True,
                                       False, False)

        mock_ack.return_value = self.none
        try:
            self.test_github_alerter._initialise_rabbitmq()
            blocking_channel = self.test_github_alerter.rabbitmq.channel

            method_chains = pika.spec.Basic.Deliver(
                routing_key=GITHUB_ALERTER_INPUT_ROUTING_KEY)

            properties = pika.spec.BasicProperties()
            self.test_github_alerter._process_data(
                blocking_channel,
                method_chains,
                properties,
                self.github_json
            )

            mock_new_github_release.assert_called_once_with(
                self.repo_name, "PANIC v2.0.2", "2.0.2",
                self.info, self.last_monitored, self.parent_id,
                self.repo_id
            )
            mock_basic_publish_confirm.assert_called()
            self.test_github_alerter.disconnect_from_rabbit()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.alerter.RabbitMQApi.basic_publish_confirm", autospec=True)
    @mock.patch("src.alerter.alerters.alerter.RabbitMQApi.basic_ack", autospec=True)
    @mock.patch("src.alerter.alerters.github.NewGitHubReleaseAlert", autospec=True)
    def test_first_run_no_github_alerts_previous_is_none(
            self, mock_new_github_release, mock_ack, mock_basic_publish_confirm):
        self.rabbitmq.connect_till_successful()
        self.rabbitmq.exchange_declare(ALERT_EXCHANGE, "topic", False, True,
                                       False, False)

        mock_ack.return_value = self.none
        try:
            self.test_github_alerter._initialise_rabbitmq()
            blocking_channel = self.test_github_alerter.rabbitmq.channel

            method_chains = pika.spec.Basic.Deliver(
                routing_key=GITHUB_ALERTER_INPUT_ROUTING_KEY)

            self.github_data_received['result']['data']['no_of_releases']['previous'] = self.none
            properties = pika.spec.BasicProperties()
            self.test_github_alerter._process_data(
                blocking_channel,
                method_chains,
                properties,
                json.dumps(self.github_data_received).encode('utf-8')
            )

            mock_new_github_release.assert_not_called()
            mock_basic_publish_confirm.assert_called_once()
            self.test_github_alerter.disconnect_from_rabbit()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.alerter.RabbitMQApi.basic_publish_confirm", autospec=True)
    @mock.patch("src.alerter.alerters.alerter.RabbitMQApi.basic_ack", autospec=True)
    @mock.patch("src.alerter.alerters.github.NewGitHubReleaseAlert", autospec=True)
    def test_run_5_github_alerts_previous_is_0(
            self, mock_new_github_release, mock_ack, mock_basic_publish_confirm):
        self.rabbitmq.connect_till_successful()
        self.rabbitmq.exchange_declare(ALERT_EXCHANGE, "topic", False, True,
                                       False, False)

        mock_ack.return_value = self.none
        try:
            self.test_github_alerter._initialise_rabbitmq()
            blocking_channel = self.test_github_alerter.rabbitmq.channel

            method_chains = pika.spec.Basic.Deliver(
                routing_key=GITHUB_ALERTER_INPUT_ROUTING_KEY)

            self.github_data_received['result']['data']['no_of_releases']['previous'] = 0

            properties = pika.spec.BasicProperties()
            self.test_github_alerter._process_data(
                blocking_channel,
                method_chains,
                properties,
                json.dumps(self.github_data_received).encode('utf-8')
            )

            self.assertEqual(5, mock_new_github_release.call_count)
            self.assertEqual(6, mock_basic_publish_confirm.call_count)
            self.test_github_alerter.disconnect_from_rabbit()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.alerter.RabbitMQApi.basic_publish_confirm", autospec=True)
    @mock.patch("src.alerter.alerters.alerter.RabbitMQApi.basic_ack", autospec=True)
    @mock.patch("src.alerter.alerters.github.NewGitHubReleaseAlert", autospec=True)
    def test_run_no_github_alerts_previous_is_5(
            self, mock_new_github_release, mock_ack, mock_basic_publish_confirm):
        self.rabbitmq.connect_till_successful()
        self.rabbitmq.exchange_declare(ALERT_EXCHANGE, "topic", False, True,
                                       False, False)

        mock_ack.return_value = self.none
        try:
            self.test_github_alerter._initialise_rabbitmq()
            blocking_channel = self.test_github_alerter.rabbitmq.channel

            method_chains = pika.spec.Basic.Deliver(
                routing_key=GITHUB_ALERTER_INPUT_ROUTING_KEY)

            self.github_data_received['result']['data']['no_of_releases']['previous'] = 5

            properties = pika.spec.BasicProperties()
            self.test_github_alerter._process_data(
                blocking_channel,
                method_chains,
                properties,
                json.dumps(self.github_data_received).encode('utf-8')
            )

            self.assertEqual(0, mock_new_github_release.call_count)
            self.assertEqual(1, mock_basic_publish_confirm.call_count)
            self.test_github_alerter.disconnect_from_rabbit()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.alerter.RabbitMQApi.basic_publish_confirm", autospec=True)
    @mock.patch("src.alerter.alerters.alerter.RabbitMQApi.basic_ack", autospec=True)
    @mock.patch("src.alerter.alerters.github.CannotAccessGitHubPageAlert", autospec=True)
    def test_cannot_access_github_page_alert(
            self, mock_cannot_access_github_page_alert, mock_ack, mock_basic_publish_confirm):
        self.rabbitmq.connect_till_successful()
        self.rabbitmq.exchange_declare(ALERT_EXCHANGE, "topic", False, True,
                                       False, False)

        mock_ack.return_value = self.none
        try:
            self.test_github_alerter._initialise_rabbitmq()
            blocking_channel = self.test_github_alerter.rabbitmq.channel

            method_chains = pika.spec.Basic.Deliver(
                routing_key=GITHUB_ALERTER_INPUT_ROUTING_KEY)

            properties = pika.spec.BasicProperties()
            self.test_github_alerter._process_data(
                blocking_channel,
                method_chains,
                properties,
                json.dumps(self.github_data_error).encode('utf-8')
            )

            mock_cannot_access_github_page_alert.assert_called_once_with(
                self.repo_name, self.error, self.last_monitored,
                self.parent_id, self.repo_id
            )

            self.assertEqual(2, mock_basic_publish_confirm.call_count)
            self.test_github_alerter.disconnect_from_rabbit()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.alerter.RabbitMQApi.basic_publish_confirm", autospec=True)
    @mock.patch("src.alerter.alerters.alerter.RabbitMQApi.basic_ack", autospec=True)
    @mock.patch("src.alerter.alerters.github.ReceivedUnexpectedDataException", autospec=True)
    def test_received_unexpected_data_alert(
            self, mock_received_unexpected_data_alert, mock_ack, mock_basic_publish_confirm):
        self.rabbitmq.connect_till_successful()
        self.rabbitmq.exchange_declare(ALERT_EXCHANGE, "topic", False, True,
                                       False, False)

        mock_ack.return_value = self.none
        try:
            self.test_github_alerter._initialise_rabbitmq()
            blocking_channel = self.test_github_alerter.rabbitmq.channel

            method_chains = pika.spec.Basic.Deliver(
                routing_key=GITHUB_ALERTER_INPUT_ROUTING_KEY)

            properties = pika.spec.BasicProperties()
            self.github_data_error = "unknown"
            self.test_github_alerter._process_data(
                blocking_channel,
                method_chains,
                properties,
                json.dumps(self.github_data_error).encode('utf-8')
            )

            mock_received_unexpected_data_alert.assert_called_once()
            self.assertEqual(0, mock_basic_publish_confirm.call_count)
            self.test_github_alerter.disconnect_from_rabbit()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    # Same test that is in monitors tests
    def test_send_heartbeat_sends_a_heartbeat_correctly(self) -> None:
        try:
            self.test_github_alerter._initialise_rabbitmq()
            self.test_github_alerter.rabbitmq.queue_delete(self.heartbeat_queue)

            res = self.test_github_alerter.rabbitmq.queue_declare(
                queue=self.heartbeat_queue, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_github_alerter.rabbitmq.queue_bind(
                queue=self.heartbeat_queue, exchange=HEALTH_CHECK_EXCHANGE,
                routing_key='heartbeat.worker')
            self.test_github_alerter._send_heartbeat(self.heartbeat_test)

            res = self.test_github_alerter.rabbitmq.queue_declare(
                queue=self.heartbeat_queue, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            self.assertEqual(1, res.method.message_count)

            _, _, body = self.test_github_alerter.rabbitmq.basic_get(
                self.heartbeat_queue)
            self.assertEqual(self.heartbeat_test, json.loads(body))

            self.test_github_alerter.rabbitmq.queue_purge(self.heartbeat_queue)
            self.test_github_alerter.rabbitmq.queue_delete(self.heartbeat_queue)
            self.test_github_alerter.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
            self.test_github_alerter.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.alerter.RabbitMQApi.basic_publish_confirm", autospec=True)
    @mock.patch("src.alerter.alerters.alerter.RabbitMQApi.basic_ack", autospec=True)
    @mock.patch("src.alerter.alerters.github.Alerter._send_heartbeat", autospec=True)
    def test_heart_beat_is_being_sent(
            self, mock_send_heartbeat, mock_ack,mock_basic_publish_confirm):
        self.rabbitmq.connect_till_successful()
        self.rabbitmq.exchange_declare(ALERT_EXCHANGE, "topic", False, True,
                                       False, False)

        mock_ack.return_value = self.none
        try:
            self.test_github_alerter._initialise_rabbitmq()
            blocking_channel = self.test_github_alerter.rabbitmq.channel

            method_chains = pika.spec.Basic.Deliver(
                routing_key=GITHUB_ALERTER_INPUT_ROUTING_KEY)

            properties = pika.spec.BasicProperties()
            self.test_github_alerter._process_data(
                blocking_channel,
                method_chains,
                properties,
                self.github_json
            )

            mock_send_heartbeat.assert_called_once()
            mock_basic_publish_confirm.assert_called()
            self.test_github_alerter.disconnect_from_rabbit()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.alerter.RabbitMQApi.basic_publish_confirm", autospec=True)
    @mock.patch("src.alerter.alerters.alerter.RabbitMQApi.basic_ack", autospec=True)
    @mock.patch("src.alerter.alerters.github.GithubAlerter._place_latest_data_on_queue", autospec=True)
    def test_place_latest_data_on_queue(
            self, mock_place_latest_data_on_queue,
            mock_ack, mock_basic_publish_confirm):
        self.rabbitmq.connect_till_successful()
        self.rabbitmq.exchange_declare(ALERT_EXCHANGE, "topic", False, True,
                                       False, False)

        mock_ack.return_value = self.none
        try:
            self.test_github_alerter._initialise_rabbitmq()
            blocking_channel = self.test_github_alerter.rabbitmq.channel

            method_chains = pika.spec.Basic.Deliver(
                routing_key=GITHUB_ALERTER_INPUT_ROUTING_KEY)

            properties = pika.spec.BasicProperties()
            self.test_github_alerter._process_data(
                blocking_channel,
                method_chains,
                properties,
                self.github_json
            )

            mock_place_latest_data_on_queue.assert_called_once()
            mock_basic_publish_confirm.assert_called()
            self.test_github_alerter.disconnect_from_rabbit()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerters.alerter.RabbitMQApi.basic_publish_confirm", autospec=True)
    @mock.patch("src.alerter.alerters.alerter.RabbitMQApi.basic_ack", autospec=True)
    @mock.patch("src.alerter.alerters.github.Alerter._send_data", autospec=True)
    def test_send_data(
            self, mock_send_data, mock_ack,
            mock_basic_publish_confirm):
        self.rabbitmq.connect_till_successful()
        self.rabbitmq.exchange_declare(ALERT_EXCHANGE, "topic", False, True,
                                       False, False)

        mock_ack.return_value = self.none
        try:
            self.test_github_alerter._initialise_rabbitmq()
            blocking_channel = self.test_github_alerter.rabbitmq.channel

            method_chains = pika.spec.Basic.Deliver(
                routing_key=GITHUB_ALERTER_INPUT_ROUTING_KEY)

            properties = pika.spec.BasicProperties()
            self.test_github_alerter._process_data(
                blocking_channel,
                method_chains,
                properties,
                self.github_json
            )

            mock_send_data.assert_called_once()
            mock_basic_publish_confirm.assert_called_once()
            self.test_github_alerter.disconnect_from_rabbit()
        except Exception as e:
            self.fail("Test failed: {}".format(e))