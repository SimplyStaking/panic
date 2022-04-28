import copy
import datetime
import json
import logging
import unittest
from queue import Queue
from unittest import mock
from unittest.mock import call

import pika
from freezegun import freeze_time

from src.alerter.alerters.dockerhub import DockerhubAlerter
from src.alerter.alerts.dockerhub_alerts import (
    DockerHubNewTagAlert
)
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.rabbitmq import (
    ALERT_EXCHANGE, DOCKERHUB_ALERTER_INPUT_QUEUE_NAME,
    DOCKERHUB_ALERT_ROUTING_KEY, HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY,
    DOCKERHUB_TRANSFORMED_DATA_ROUTING_KEY, HEALTH_CHECK_EXCHANGE)
from src.utils.env import ALERTER_PUBLISHING_QUEUE_SIZE, RABBIT_IP
from test.test_utils.utils import (
    connect_to_rabbit, delete_queue_if_exists, disconnect_from_rabbit,
    delete_exchange_if_exists)


class TestDockerhubAlerter(unittest.TestCase):
    def setUp(self) -> None:
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = datetime.timedelta(seconds=0)
        self.alert_input_exchange = ALERT_EXCHANGE

        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, RABBIT_IP,
            connection_check_time_interval=self.connection_check_time_interval)

        self.test_rabbit_manager = RabbitMQApi(
            self.dummy_logger, RABBIT_IP,
            connection_check_time_interval=self.connection_check_time_interval)

        self.alerter_name = 'test_dockerhub_alerter'
        self.repo_namespace = 'simplyvc'
        self.repo_name = 'panic'
        self.repo_id = 'test_repo_id'
        self.parent_id = 'test_parent_id'
        self.dockerhub_name = 'test_dockerhub'
        self.error_message = 'error message'
        self.last_monitored = 1611619200
        self.publishing_queue = Queue(ALERTER_PUBLISHING_QUEUE_SIZE)
        self.test_routing_key = 'test_alert.dockerhub'
        self.output_routing_key = DOCKERHUB_ALERT_ROUTING_KEY
        self.test_dockerhub_alerter = DockerhubAlerter(
            self.alerter_name,
            self.dummy_logger,
            self.rabbitmq,
            ALERTER_PUBLISHING_QUEUE_SIZE
        )

        self.warning = "WARNING"
        self.info = "INFO"
        self.critical = "CRITICAL"
        self.error = "ERROR"
        self.none = None

        self.heartbeat_test = {
            'component_name': self.alerter_name,
            'is_alive': True,
            'timestamp': datetime.datetime(2012, 1, 1).timestamp()
        }
        self.heartbeat_queue = 'heartbeat queue'

        """
        ################# Metrics Received from Data Transformer ############
        """
        self.dockerhub_data_received = {
            "result": {
                "meta_data": {
                    "repo_namespace": self.repo_namespace,
                    "repo_name": self.repo_name,
                    "repo_id": self.repo_id,
                    "repo_parent_id": self.parent_id,
                    "last_monitored": self.last_monitored
                },
                "data": {
                    "current": {
                        '0': {
                            'tag_name': 'v2.0.0',
                            'last_updated': 1635498220.012198
                        },
                        '1': {
                            'tag_name': 'v1.0.0',
                            'last_updated': 1635229653
                        },
                        '2': {
                            'tag_name': 'v0.4.0',
                            'last_updated': 1632637653
                        },
                        '3': {
                            'tag_name': 'v0.3.0',
                            'last_updated': 1635498220
                        },
                    },
                    "previous": {
                        '0': {
                            'tag_name': 'v1.0.0',
                            'last_updated': 1635229653
                        },
                        '1': {
                            'tag_name': 'v0.4.0',
                            'last_updated': 1632637653
                        },
                        '2': {
                            'tag_name': 'v0.3.0',
                            'last_updated': 1629959253
                        },
                        '3': {
                            'tag_name': 'v0.2.0',
                            'last_updated': 1629280853.0214
                        },
                    }
                }
            }
        }
        self.dockerhub_json = json.dumps(self.dockerhub_data_received)
        self.frozen_timestamp = datetime.datetime(2012, 1, 1).timestamp()
        self.dockerhub_data_error = {
            "error": {
                "meta_data": {
                    "repo_namespace": self.repo_namespace,
                    "repo_name": self.repo_name,
                    "repo_id": self.repo_id,
                    "repo_parent_id": self.parent_id,
                    "time": self.last_monitored
                },
                "code": "5021",
                "message": "error message"
            }
        }
        self.dockerhub_json_error = json.dumps(self.dockerhub_data_error)

        self.dockerhub_api_error = copy.deepcopy(self.dockerhub_data_error)
        self.dockerhub_api_error['error']['code'] = '5020'
        self.dockerhub_api_error['error']['message'] = self.error_message

        # Alert used for rabbitMQ testing
        self.alert = DockerHubNewTagAlert(
            self.repo_namespace, self.repo_name, "PANIC_TAG", self.info,
            self.last_monitored, self.parent_id, self.repo_id
        )

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        connect_to_rabbit(self.test_dockerhub_alerter.rabbitmq)
        delete_queue_if_exists(self.test_dockerhub_alerter.rabbitmq,
                               DOCKERHUB_ALERTER_INPUT_QUEUE_NAME)
        delete_exchange_if_exists(self.test_dockerhub_alerter.rabbitmq,
                                  ALERT_EXCHANGE)
        delete_exchange_if_exists(self.test_dockerhub_alerter.rabbitmq,
                                  HEALTH_CHECK_EXCHANGE)
        disconnect_from_rabbit(self.test_dockerhub_alerter.rabbitmq)

        self.dummy_logger = None
        self.rabbitmq = None
        self.publishing_queue = None
        self.test_dockerhub_alerter = None
        self.dockerhub_data_received = None
        self.test_rabbit_manager = None

    def test_str_returns_alerter_name_as_string(self) -> None:
        self.assertEqual(self.alerter_name,
                         str(self.test_dockerhub_alerter))

    def test_alerter_name_returns_alerter_name(self) -> None:
        self.assertEqual(self.alerter_name,
                         self.test_dockerhub_alerter.alerter_name)

    def test_logger_returns_logger(self) -> None:
        self.assertEqual(self.dummy_logger, self.test_dockerhub_alerter.logger)

    def test_publishing_queue_size_is_as_expected(self) -> None:
        self.assertEqual(self.publishing_queue.qsize(),
                         self.test_dockerhub_alerter.publishing_queue.qsize())

    """
    ###################### Tests using RabbitMQ #######################
    """

    def test_initialise_rabbit_initialises_queues(self) -> None:
        self.test_dockerhub_alerter._initialise_rabbitmq()
        self.rabbitmq.connect()
        self.rabbitmq.queue_declare(DOCKERHUB_ALERTER_INPUT_QUEUE_NAME,
                                    passive=True)

    def test_initialise_rabbit_initialises_exchanges(self) -> None:
        self.test_dockerhub_alerter._initialise_rabbitmq()
        self.rabbitmq.connect()
        self.rabbitmq.exchange_declare(ALERT_EXCHANGE, passive=True)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, passive=True)

    @mock.patch(
        "src.alerter.alerters.alerter.RabbitMQApi.basic_publish_confirm",
        autospec=True)
    @mock.patch("src.alerter.alerters.alerter.RabbitMQApi.basic_ack",
                autospec=True)
    @mock.patch(
        "src.alerter.alerters.dockerhub.DockerHubPageNowAccessibleAlert",
        autospec=True)
    @mock.patch("src.alerter.alerters.dockerhub.DockerHubNewTagAlert",
                autospec=True)
    @mock.patch("src.alerter.alerters.dockerhub.DockerHubUpdatedTagAlert",
                autospec=True)
    @mock.patch("src.alerter.alerters.dockerhub.DockerHubDeletedTagAlert",
                autospec=True)
    def test_different_dockerhub_alerts(
            self, mock_deleted_dockerhub_tag, mock_updated_dockerhub_tag,
            mock_new_dockerhub_tag, mock_dockerhub_access, mock_ack,
            mock_basic_publish_confirm):
        self.rabbitmq.connect()
        self.rabbitmq.exchange_declare(ALERT_EXCHANGE, "topic", False, True,
                                       False, False)
        type(mock_new_dockerhub_tag.return_value).alert_data = \
            mock.PropertyMock(return_value={})
        type(mock_updated_dockerhub_tag.return_value).alert_data = \
            mock.PropertyMock(return_value={})
        type(mock_deleted_dockerhub_tag.return_value).alert_data = \
            mock.PropertyMock(return_value={})
        type(mock_dockerhub_access.return_value).alert_data = \
            mock.PropertyMock(return_value={})
        mock_ack.return_value = self.none

        self.test_dockerhub_alerter._initialise_rabbitmq()
        blocking_channel = self.test_dockerhub_alerter.rabbitmq.channel

        method_chains = pika.spec.Basic.Deliver(
            routing_key=DOCKERHUB_TRANSFORMED_DATA_ROUTING_KEY)

        properties = pika.spec.BasicProperties()
        self.test_dockerhub_alerter._process_data(
            blocking_channel,
            method_chains,
            properties,
            self.dockerhub_json
        )

        mock_new_dockerhub_tag.assert_called_once_with(
            self.repo_namespace, self.repo_name, "v2.0.0",
            self.info, self.last_monitored, self.parent_id,
            self.repo_id
        )
        mock_updated_dockerhub_tag.assert_called_once_with(
            self.repo_namespace, self.repo_name, "v0.3.0",
            self.info, self.last_monitored, self.parent_id,
            self.repo_id
        )
        mock_deleted_dockerhub_tag.assert_called_once_with(
            self.repo_namespace, self.repo_name, "v0.2.0",
            self.info, self.last_monitored, self.parent_id,
            self.repo_id
        )
        mock_dockerhub_access.assert_not_called()
        mock_basic_publish_confirm.assert_called()

    @mock.patch(
        "src.alerter.alerters.alerter.RabbitMQApi.basic_publish_confirm",
        autospec=True)
    @mock.patch("src.alerter.alerters.alerter.RabbitMQApi.basic_ack",
                autospec=True)
    @mock.patch(
        "src.alerter.alerters.dockerhub.DockerHubPageNowAccessibleAlert",
        autospec=True)
    @mock.patch("src.alerter.alerters.dockerhub.DockerHubNewTagAlert",
                autospec=True)
    @mock.patch("src.alerter.alerters.dockerhub.DockerHubUpdatedTagAlert",
                autospec=True)
    @mock.patch("src.alerter.alerters.dockerhub.DockerHubDeletedTagAlert",
                autospec=True)
    def test_first_run_no_new_release_dockerhub_alerts(
            self, mock_deleted_dockerhub_tag, mock_updated_dockerhub_tag,
            mock_new_dockerhub_tag, mock_dockerhub_access, mock_ack,
            mock_basic_publish_confirm):
        self.rabbitmq.connect()
        self.rabbitmq.exchange_declare(ALERT_EXCHANGE, "topic", False, True,
                                       False, False)
        type(mock_dockerhub_access.return_value).alert_data = \
            mock.PropertyMock(return_value={})
        mock_ack.return_value = self.none

        self.test_dockerhub_alerter._initialise_rabbitmq()
        blocking_channel = self.test_dockerhub_alerter.rabbitmq.channel

        method_chains = pika.spec.Basic.Deliver(
            routing_key=DOCKERHUB_TRANSFORMED_DATA_ROUTING_KEY)

        self.dockerhub_data_received['result']['data']['previous'] = None
        properties = pika.spec.BasicProperties()
        self.test_dockerhub_alerter._process_data(
            blocking_channel,
            method_chains,
            properties,
            json.dumps(self.dockerhub_data_received)
        )
        mock_new_dockerhub_tag.assert_not_called()
        mock_updated_dockerhub_tag.assert_not_called()
        mock_deleted_dockerhub_tag.assert_not_called()
        mock_dockerhub_access.assert_not_called()
        self.assertEqual(1, mock_basic_publish_confirm.call_count)

    @mock.patch(
        "src.alerter.alerters.alerter.RabbitMQApi.basic_publish_confirm",
        autospec=True)
    @mock.patch("src.alerter.alerters.alerter.RabbitMQApi.basic_ack",
                autospec=True)
    @mock.patch(
        "src.alerter.alerters.dockerhub.DockerHubPageNowAccessibleAlert",
        autospec=True)
    @mock.patch("src.alerter.alerters.dockerhub.DockerHubNewTagAlert",
                autospec=True)
    @mock.patch("src.alerter.alerters.dockerhub.DockerHubUpdatedTagAlert",
                autospec=True)
    @mock.patch("src.alerter.alerters.dockerhub.DockerHubDeletedTagAlert",
                autospec=True)
    def test_run_3_dockerhub_alerts_previous_is_1(
            self, mock_deleted_dockerhub_tag, mock_updated_dockerhub_tag,
            mock_new_dockerhub_tag, mock_dockerhub_access, mock_ack,
            mock_basic_publish_confirm):
        self.rabbitmq.connect()
        self.rabbitmq.exchange_declare(ALERT_EXCHANGE, "topic", False, True,
                                       False, False)

        type(mock_deleted_dockerhub_tag.return_value).alert_data = \
            mock.PropertyMock(return_value={})
        type(mock_updated_dockerhub_tag.return_value).alert_data = \
            mock.PropertyMock(return_value={})
        type(mock_new_dockerhub_tag.return_value).alert_data = \
            mock.PropertyMock(return_value={})
        type(mock_dockerhub_access.return_value).alert_data = \
            mock.PropertyMock(return_value={})
        mock_ack.return_value = self.none

        self.test_dockerhub_alerter._initialise_rabbitmq()
        blocking_channel = self.test_dockerhub_alerter.rabbitmq.channel

        method_chains = pika.spec.Basic.Deliver(
            routing_key=DOCKERHUB_TRANSFORMED_DATA_ROUTING_KEY)

        self.dockerhub_data_received['result']['data']['previous'] = \
            {
                '0': {
                    'tag_name': 'v0.3.0',
                    'last_updated': 1635498220
                }
            }

        properties = pika.spec.BasicProperties()
        self.test_dockerhub_alerter._process_data(
            blocking_channel,
            method_chains,
            properties,
            json.dumps(self.dockerhub_data_received)
        )
        call_1 = call(self.repo_namespace, self.repo_name, "v2.0.0",
                      self.info, self.last_monitored, self.parent_id,
                      self.repo_id)
        call_2 = call(self.repo_namespace, self.repo_name, "v1.0.0",
                      self.info, self.last_monitored, self.parent_id,
                      self.repo_id)
        call_3 = call(self.repo_namespace, self.repo_name, "v0.4.0",
                      self.info, self.last_monitored, self.parent_id,
                      self.repo_id)

        mock_new_dockerhub_tag.assert_has_calls([call_1, call_2, call_3])
        mock_dockerhub_access.assert_not_called()
        mock_updated_dockerhub_tag.assert_not_called()
        mock_deleted_dockerhub_tag.assert_not_called()
        # Call count of basic_publish_confirm is higher than
        # dockerhub_release call_count because of the hb and initial
        # validation alerts
        self.assertEqual(3, mock_new_dockerhub_tag.call_count)
        self.assertEqual(4, mock_basic_publish_confirm.call_count)

    @mock.patch(
        "src.alerter.alerters.alerter.RabbitMQApi.basic_publish_confirm",
        autospec=True)
    @mock.patch("src.alerter.alerters.alerter.RabbitMQApi.basic_ack",
                autospec=True)
    @mock.patch("src.alerter.alerters.dockerhub.CannotAccessDockerHubPageAlert",
                autospec=True)
    def test_cannot_access_dockerhub_page_alert(
            self, mock_cannot_access_dockerhub_page_alert, mock_ack,
            mock_basic_publish_confirm):
        self.rabbitmq.connect()
        self.rabbitmq.exchange_declare(ALERT_EXCHANGE, "topic", False, True,
                                       False, False)

        type(
            mock_cannot_access_dockerhub_page_alert.return_value
        ).alert_data = mock.PropertyMock(return_value={})
        mock_ack.return_value = self.none

        self.test_dockerhub_alerter._initialise_rabbitmq()
        blocking_channel = self.test_dockerhub_alerter.rabbitmq.channel

        method_chains = pika.spec.Basic.Deliver(
            routing_key=DOCKERHUB_TRANSFORMED_DATA_ROUTING_KEY)

        properties = pika.spec.BasicProperties()
        self.test_dockerhub_alerter._process_data(
            blocking_channel,
            method_chains,
            properties,
            json.dumps(self.dockerhub_data_error)
        )

        mock_cannot_access_dockerhub_page_alert.assert_called_once_with(
            self.repo_namespace, self.repo_name, self.error,
            self.last_monitored, self.parent_id, self.repo_id
        )

        self.assertEqual(2, mock_basic_publish_confirm.call_count)

    @mock.patch(
        "src.alerter.alerters.alerter.RabbitMQApi.basic_publish_confirm",
        autospec=True)
    @mock.patch("src.alerter.alerters.alerter.RabbitMQApi.basic_ack",
                autospec=True)
    @mock.patch("src.alerter.alerters.dockerhub.DockerHubTagsAPICallErrorAlert",
                autospec=True)
    def test_cannot_access_dockerhub_tag_api_alert(
            self, dockerhub_tags_api_call_error_alert, mock_ack,
            mock_basic_publish_confirm):
        self.rabbitmq.connect()
        self.rabbitmq.exchange_declare(ALERT_EXCHANGE, "topic", False, True,
                                       False, False)

        type(
            dockerhub_tags_api_call_error_alert.return_value
        ).alert_data = mock.PropertyMock(return_value={})
        mock_ack.return_value = self.none

        self.test_dockerhub_alerter._initialise_rabbitmq()
        blocking_channel = self.test_dockerhub_alerter.rabbitmq.channel

        method_chains = pika.spec.Basic.Deliver(
            routing_key=DOCKERHUB_TRANSFORMED_DATA_ROUTING_KEY)

        properties = pika.spec.BasicProperties()
        self.test_dockerhub_alerter._process_data(
            blocking_channel,
            method_chains,
            properties,
            json.dumps(self.dockerhub_api_error)
        )

        dockerhub_tags_api_call_error_alert.assert_called_once_with(
            self.repo_namespace, self.repo_name, self.error,
            self.last_monitored, self.parent_id, self.repo_id,
            self.error_message
        )

        self.assertEqual(2, mock_basic_publish_confirm.call_count)
        self.assertEqual(
            {self.repo_id: True},
            self.test_dockerhub_alerter._tags_api_call_error)

    @mock.patch(
        "src.alerter.alerters.alerter.RabbitMQApi.basic_publish_confirm",
        autospec=True)
    @mock.patch("src.alerter.alerters.alerter.RabbitMQApi.basic_ack",
                autospec=True)
    @mock.patch(
        "src.alerter.alerters.dockerhub.ReceivedUnexpectedDataException",
        autospec=True)
    def test_received_unexpected_data_error(
            self, mock_received_unexpected_data_error, mock_ack,
            mock_basic_publish_confirm):
        self.rabbitmq.connect()
        self.rabbitmq.exchange_declare(ALERT_EXCHANGE, "topic", False, True,
                                       False, False)

        mock_ack.return_value = self.none

        self.test_dockerhub_alerter._initialise_rabbitmq()
        blocking_channel = self.test_dockerhub_alerter.rabbitmq.channel

        method_chains = pika.spec.Basic.Deliver(
            routing_key=DOCKERHUB_TRANSFORMED_DATA_ROUTING_KEY)

        properties = pika.spec.BasicProperties()
        dockerhub_data_error = "unknown"
        self.test_dockerhub_alerter._process_data(
            blocking_channel,
            method_chains,
            properties,
            json.dumps(dockerhub_data_error)
        )

        mock_received_unexpected_data_error.assert_called_once()
        self.assertEqual(0, mock_basic_publish_confirm.call_count)

    # Same test that is in monitors tests
    def test_send_heartbeat_sends_a_heartbeat_correctly(self) -> None:
        self.test_rabbit_manager.connect()
        self.test_dockerhub_alerter._initialise_rabbitmq()
        self.test_dockerhub_alerter.rabbitmq.queue_delete(
            self.heartbeat_queue)
        res = self.test_rabbit_manager.queue_declare(
            queue=self.heartbeat_queue, durable=True, exclusive=False,
            auto_delete=False, passive=False
        )
        self.assertEqual(0, res.method.message_count)
        self.test_rabbit_manager.queue_bind(
            queue=self.heartbeat_queue, exchange=HEALTH_CHECK_EXCHANGE,
            routing_key=HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY)
        self.test_dockerhub_alerter._send_heartbeat(self.heartbeat_test)

        res = self.test_rabbit_manager.queue_declare(
            queue=self.heartbeat_queue, durable=True, exclusive=False,
            auto_delete=False, passive=True
        )
        self.assertEqual(1, res.method.message_count)

        _, _, body = self.test_rabbit_manager.basic_get(
            self.heartbeat_queue)
        self.assertEqual(self.heartbeat_test, json.loads(body))

    @freeze_time("2012-01-01")
    @mock.patch(
        "src.alerter.alerters.alerter.RabbitMQApi.basic_publish_confirm",
        autospec=True)
    @mock.patch("src.alerter.alerters.alerter.RabbitMQApi.basic_ack",
                autospec=True)
    @mock.patch("src.alerter.alerters.dockerhub.Alerter._send_heartbeat",
                autospec=True)
    def test_heartbeat_is_being_sent_no_errors(
            self, mock_send_heartbeat, mock_ack, mock_basic_publish_confirm):
        self.rabbitmq.connect()
        self.rabbitmq.exchange_declare(ALERT_EXCHANGE, "topic", False, True,
                                       False, False)

        mock_ack.return_value = self.none

        self.test_dockerhub_alerter._initialise_rabbitmq()
        blocking_channel = self.test_dockerhub_alerter.rabbitmq.channel

        method_chains = pika.spec.Basic.Deliver(
            routing_key=DOCKERHUB_TRANSFORMED_DATA_ROUTING_KEY)

        properties = pika.spec.BasicProperties()
        self.test_dockerhub_alerter._process_data(
            blocking_channel,
            method_chains,
            properties,
            self.dockerhub_json
        )

        args, _ = mock_send_heartbeat.call_args
        self.assertEqual(args[1]['component_name'], self.alerter_name)
        self.assertEqual(args[1]['is_alive'], True)
        self.assertEqual(args[1]['timestamp'],
                         datetime.datetime(2012, 1, 1).timestamp())
        mock_basic_publish_confirm.assert_called()

    @mock.patch(
        "src.alerter.alerters.alerter.RabbitMQApi.basic_publish_confirm",
        autospec=True)
    @mock.patch("src.alerter.alerters.alerter.RabbitMQApi.basic_ack",
                autospec=True)
    @mock.patch(
        "src.alerter.alerters.dockerhub.DockerhubAlerter"
        "._place_latest_data_on_queue",
        autospec=True)
    def test_place_latest_data_on_queue_called_once_when_no_errors(
            self, mock_place_latest_data_on_queue,
            mock_ack, mock_basic_publish_confirm):
        self.rabbitmq.connect()
        self.rabbitmq.exchange_declare(ALERT_EXCHANGE, "topic", False, True,
                                       False, False)

        mock_ack.return_value = self.none
        mock_basic_publish_confirm.return_value = self.none

        self.test_dockerhub_alerter._initialise_rabbitmq()
        blocking_channel = self.test_dockerhub_alerter.rabbitmq.channel

        method_chains = pika.spec.Basic.Deliver(
            routing_key=DOCKERHUB_TRANSFORMED_DATA_ROUTING_KEY)

        properties = pika.spec.BasicProperties()
        self.test_dockerhub_alerter._process_data(
            blocking_channel,
            method_chains,
            properties,
            self.dockerhub_json
        )

        mock_place_latest_data_on_queue.assert_called_once()

    @mock.patch(
        "src.alerter.alerters.alerter.RabbitMQApi.basic_publish_confirm",
        autospec=True)
    @mock.patch("src.alerter.alerters.alerter.RabbitMQApi.basic_ack",
                autospec=True)
    def test_send_data_works_correctly(
            self, mock_ack, mock_basic_publish_confirm):
        self.rabbitmq.connect()
        self.rabbitmq.exchange_declare(ALERT_EXCHANGE, "topic", False, True,
                                       False, False)
        mock_ack.return_value = self.none
        self.test_dockerhub_alerter._place_latest_data_on_queue(
            [self.alert.alert_data])
        self.test_dockerhub_alerter._send_data()
        mock_basic_publish_confirm.assert_called_once()
