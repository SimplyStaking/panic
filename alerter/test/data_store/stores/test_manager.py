import json
import logging
import multiprocessing
import unittest
from datetime import timedelta, datetime
from unittest import mock

import pika
import pika.exceptions
from freezegun import freeze_time
from parameterized import parameterized

from src.data_store.starters import (start_system_store, start_github_store,
                                     start_chainlink_node_store,
                                     start_alert_store, start_config_store,
                                     start_evm_node_store,
                                     start_cl_contract_store)
from src.data_store.stores.manager import StoreManager
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants.names import (SYSTEM_STORE_NAME, GITHUB_STORE_NAME,
                                       ALERT_STORE_NAME, CONFIG_STORE_NAME,
                                       CL_NODE_STORE_NAME, EVM_NODE_STORE_NAME,
                                       CL_CONTRACT_STORE_NAME)
from src.utils.constants.rabbitmq import (HEALTH_CHECK_EXCHANGE,
                                          DATA_STORES_MAN_HEARTBEAT_QUEUE_NAME,
                                          PING_ROUTING_KEY,
                                          HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY)
from src.utils.exceptions import PANICException, MessageWasNotDeliveredException
from test.utils.utils import (infinite_fn, connect_to_rabbit,
                              delete_queue_if_exists, delete_exchange_if_exists,
                              disconnect_from_rabbit)


class TestStoreManager(unittest.TestCase):
    def setUp(self) -> None:
        # Dummy data
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.manager_name = 'test_data_stores_manager'
        self.test_queue_name = 'Test Queue'
        self.test_data_str = 'test data'
        self.test_timestamp = datetime(2012, 1, 1).timestamp()
        self.test_heartbeat = {
            'component_name': 'Test Component',
            'is_alive': True,
            'timestamp': self.test_timestamp,
        }
        self.test_exception = PANICException('test_exception', 1)

        # Rabbit Instance
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbit_ip = env.RABBIT_IP
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)

        # Dummy state
        self.dummy_process1 = multiprocessing.Process(target=infinite_fn,
                                                      args=())
        self.dummy_process1.daemon = True
        self.dummy_process2 = multiprocessing.Process(target=infinite_fn,
                                                      args=())
        self.dummy_process2.daemon = True
        self.dummy_process3 = multiprocessing.Process(target=infinite_fn,
                                                      args=())
        self.dummy_process3.daemon = True
        self.dummy_process4 = multiprocessing.Process(target=infinite_fn,
                                                      args=())
        self.dummy_process4.daemon = True
        self.dummy_process5 = multiprocessing.Process(target=infinite_fn,
                                                      args=())
        self.dummy_process5.daemon = True
        self.dummy_process6 = multiprocessing.Process(target=infinite_fn,
                                                      args=())
        self.dummy_process6.daemon = True
        self.dummy_process7 = multiprocessing.Process(target=infinite_fn,
                                                      args=())
        self.dummy_process7.daemon = True
        self.store_process_dict_example = {
            SYSTEM_STORE_NAME: self.dummy_process1,
            GITHUB_STORE_NAME: self.dummy_process2,
            ALERT_STORE_NAME: self.dummy_process3,
            CONFIG_STORE_NAME: self.dummy_process4,
            CL_NODE_STORE_NAME: self.dummy_process5,
            EVM_NODE_STORE_NAME: self.dummy_process6,
            CL_CONTRACT_STORE_NAME: self.dummy_process7
        }

        # Test data store manager
        self.test_manager = StoreManager(self.dummy_logger, self.manager_name,
                                         self.rabbitmq)

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        connect_to_rabbit(self.test_manager.rabbitmq)
        delete_queue_if_exists(self.test_manager.rabbitmq, self.test_queue_name)
        delete_queue_if_exists(self.test_manager.rabbitmq,
                               DATA_STORES_MAN_HEARTBEAT_QUEUE_NAME)
        delete_exchange_if_exists(self.test_manager.rabbitmq,
                                  HEALTH_CHECK_EXCHANGE)
        disconnect_from_rabbit(self.test_manager.rabbitmq)

        self.dummy_logger = None
        self.rabbitmq = None
        self.dummy_process1 = None
        self.dummy_process2 = None
        self.dummy_process3 = None
        self.dummy_process4 = None
        self.dummy_process5 = None
        self.dummy_process6 = None
        self.dummy_process7 = None
        self.test_manager = None
        self.test_exception = None
        self.store_process_dict_example = None

    def test_str_returns_manager_name(self) -> None:
        self.assertEqual(self.manager_name, str(self.test_manager))

    def test_name_returns_manager_name(self) -> None:
        self.assertEqual(self.manager_name, self.test_manager.name)

    def test_initialise_rabbitmq_initializes_everything_as_expected(
            self) -> None:
        # To make sure that there is no connection/channel already established
        self.assertIsNone(self.rabbitmq.connection)
        self.assertIsNone(self.rabbitmq.channel)

        # To make sure that the exchange and queue have not already been
        # declared
        self.rabbitmq.connect()
        self.test_manager.rabbitmq.queue_delete(
            DATA_STORES_MAN_HEARTBEAT_QUEUE_NAME)
        self.test_manager.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.disconnect()

        self.test_manager._initialise_rabbitmq()

        # Perform checks that the connection has been opened, marked as open
        # and that the delivery confirmation variable is set.
        self.assertTrue(self.test_manager.rabbitmq.is_connected)
        self.assertTrue(self.test_manager.rabbitmq.connection.is_open)
        self.assertTrue(
            self.test_manager.rabbitmq.channel._delivery_confirmation)

        # Check whether the exchange and queue have been creating by
        # sending messages with the same routing keys as for the queue. We
        # will also check if the size of the queue is 0 to confirm that
        # basic_consume was called (it will store the msg in the component
        # memory immediately). If one of the exchange or queue is not
        # created, then either an exception will be thrown or the queue size
        # would be 1. Note when deleting the exchange in the beginning we
        # also released every binding, hence there is no other queue binded
        # with the same routing key to any exchange at this point.
        self.test_manager.rabbitmq.basic_publish_confirm(
            exchange=HEALTH_CHECK_EXCHANGE, routing_key=PING_ROUTING_KEY,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)

        # Re-declare queue to get the number of messages
        res = self.test_manager.rabbitmq.queue_declare(
            DATA_STORES_MAN_HEARTBEAT_QUEUE_NAME, False, True, False, False)
        self.assertEqual(0, res.method.message_count)

    @mock.patch.object(RabbitMQApi, "start_consuming")
    def test_listen_for_data_calls_start_consuming(
            self, mock_start_consuming) -> None:
        mock_start_consuming.return_value = None
        self.test_manager._listen_for_data()
        mock_start_consuming.assert_called_once()

    def test_send_heartbeat_sends_a_heartbeat_correctly(self) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_heartbeat, and checks that the
        # heartbeat is received
        self.test_manager._initialise_rabbitmq()

        # Delete the queue before to avoid messages in the queue on error.
        self.test_manager.rabbitmq.queue_delete(self.test_queue_name)

        res = self.test_manager.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=False
        )
        self.assertEqual(0, res.method.message_count)
        self.test_manager.rabbitmq.queue_bind(
            queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
            routing_key=HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY)
        self.test_manager._send_heartbeat(self.test_heartbeat)

        # By re-declaring the queue again we can get the number of messages
        # in the queue.
        res = self.test_manager.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=True
        )
        self.assertEqual(1, res.method.message_count)

        # Check that the message received is actually the HB
        _, _, body = self.test_manager.rabbitmq.basic_get(
            self.test_queue_name)
        self.assertEqual(self.test_heartbeat, json.loads(body))

    @parameterized.expand([
        (SYSTEM_STORE_NAME, start_system_store, {}, False,),
        (GITHUB_STORE_NAME, start_github_store, {}, False,),
        (CL_NODE_STORE_NAME, start_chainlink_node_store, {}, False,),
        (EVM_NODE_STORE_NAME, start_evm_node_store, {}, False,),
        (CL_CONTRACT_STORE_NAME, start_cl_contract_store, {}, False,),
        (ALERT_STORE_NAME, start_alert_store, {}, False,),
        (CONFIG_STORE_NAME, start_config_store, {}, False,),
        (SYSTEM_STORE_NAME, start_system_store,
         'self.store_process_dict_example', True,),
        (GITHUB_STORE_NAME, start_github_store,
         'self.store_process_dict_example', True,),
        (CL_NODE_STORE_NAME, start_chainlink_node_store,
         'self.store_process_dict_example', True,),
        (EVM_NODE_STORE_NAME, start_evm_node_store,
         'self.store_process_dict_example', True,),
        (CL_CONTRACT_STORE_NAME, start_cl_contract_store,
         'self.store_process_dict_example', True,),
        (ALERT_STORE_NAME, start_alert_store, 'self.store_process_dict_example',
         True,),
        (CONFIG_STORE_NAME, start_config_store,
         'self.store_process_dict_example', True,),
    ])
    @mock.patch.object(multiprocessing.Process, "start")
    def test_start_stores_processes_creates_and_stores_process_correctly(
            self, store_name, store_starter, state, state_is_str,
            mock_start) -> None:
        # We will perform this test for both when the state is empty (i.e. first
        # time run, and for when the related process is dead. For the second
        # case we will use the dummy state created in startUp as no dummy
        # process was started.
        mock_start.return_value = None

        self.test_manager._store_process_dict = \
            eval(state) if state_is_str else state

        self.test_manager._start_stores_processes()

        store_process = self.test_manager._store_process_dict[store_name]
        self.assertTrue(store_process.daemon)
        self.assertEqual(0, len(store_process._args))
        self.assertEqual(store_starter, store_process._target)

    @parameterized.expand([
        ({}, False,),
        ('self.store_process_dict_example', True,),
    ])
    @mock.patch.object(multiprocessing.Process, "start")
    def test_start_stores_processes_starts_process(
            self, state, state_is_str, mock_start) -> None:
        # We will perform this test for both when the state is empty (i.e. first
        # time run, and for when the related process is dead. For the second
        # case we will use the dummy state created in startUp as no dummy
        # process was started. Note that each time we will check that start is
        # called 5 times, once for each tore.
        mock_start.return_value = None
        self.test_manager._store_process_dict = \
            eval(state) if state_is_str else state
        self.test_manager._start_stores_processes()
        self.assertEqual(7, mock_start.call_count)

    @mock.patch.object(multiprocessing, "Process")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(multiprocessing.Process, "start")
    def test_start_stores_processes_does_not_start_or_create_any_proc_if_alive(
            self, mock_start, mock_is_alive, mock_init) -> None:
        mock_start.return_value = None
        mock_is_alive.return_value = True
        mock_init.return_value = None

        # Make the state non-empty to mock the case when creation is not being
        # done for the first time
        self.test_manager._store_process_dict = self.store_process_dict_example

        self.test_manager._start_stores_processes()

        mock_start.assert_not_called()
        mock_init.assert_not_called()

    @freeze_time("2012-01-01")
    @mock.patch.object(StoreManager, "_send_heartbeat")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    def test_process_ping_sends_a_valid_hb_if_all_processes_are_alive(
            self, mock_is_alive, mock_send_hb) -> None:
        # We will perform this test by checking that send_hb is called with the
        # correct heartbeat. The actual sending was already tested above. Note
        # we wil mock is_alive by setting it to always return true to avoid
        # creating processes
        mock_is_alive.return_value = True
        mock_send_hb.return_value = None

        # Some of the variables below are needed as parameters for the
        # process_ping function
        self.test_manager._initialise_rabbitmq()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
        body = 'ping'
        properties = pika.spec.BasicProperties()

        # Make the state non-empty to mock the fact that the processes were
        # already created
        self.test_manager._store_process_dict = self.store_process_dict_example

        self.test_manager._process_ping(blocking_channel, method, properties,
                                        body)

        expected_hb = {
            'component_name': self.test_manager.name,
            'running_processes': [SYSTEM_STORE_NAME, GITHUB_STORE_NAME,
                                  ALERT_STORE_NAME, CONFIG_STORE_NAME,
                                  CL_NODE_STORE_NAME, EVM_NODE_STORE_NAME,
                                  CL_CONTRACT_STORE_NAME],
            'dead_processes': [],
            'timestamp': datetime.now().timestamp()
        }
        mock_send_hb.assert_called_once_with(expected_hb)

    @freeze_time("2012-01-01")
    @mock.patch.object(StoreManager, "_send_heartbeat")
    @mock.patch.object(StoreManager, "_start_stores_processes")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(multiprocessing.Process, "join")
    def test_process_ping_sends_a_valid_hb_if_some_processes_alive_some_dead(
            self, mock_join, mock_is_alive, mock_start_stores,
            mock_send_hb) -> None:
        # We will perform this test by checking that send_hb is called with the
        # correct heartbeat as the actual sending was already tested above. We
        # will assume that the second and third processes are dead, these
        # correspond to the github store and the alert store respectively.
        mock_is_alive.side_effect = [True, False, False, True, True, True,
                                     True]
        mock_send_hb.return_value = None
        mock_join.return_value = None
        mock_start_stores.return_value = None

        # Some of the variables below are needed as parameters for the
        # process_ping function
        self.test_manager._initialise_rabbitmq()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
        body = 'ping'
        properties = pika.spec.BasicProperties()

        # Make the state non-empty to mock the fact that the processes were
        # already created
        self.test_manager._store_process_dict = self.store_process_dict_example

        self.test_manager._process_ping(blocking_channel, method, properties,
                                        body)

        expected_hb = {
            'component_name': self.test_manager.name,
            'running_processes': [SYSTEM_STORE_NAME, CONFIG_STORE_NAME,
                                  CL_NODE_STORE_NAME, EVM_NODE_STORE_NAME,
                                  CL_CONTRACT_STORE_NAME],
            'dead_processes': [GITHUB_STORE_NAME,
                               ALERT_STORE_NAME],
            'timestamp': datetime.now().timestamp()
        }
        mock_send_hb.assert_called_once_with(expected_hb)

    @freeze_time("2012-01-01")
    @mock.patch.object(StoreManager, "_send_heartbeat")
    @mock.patch.object(StoreManager, "_start_stores_processes")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(multiprocessing.Process, "join")
    def test_process_ping_sends_a_valid_hb_if_all_processes_dead(
            self, mock_join, mock_is_alive, mock_start_stores,
            mock_send_hb) -> None:
        # We will perform this test by checking that send_hb is called with the
        # correct heartbeat as the actual sending was already tested above. Note
        # we wil mock is_alive by setting it to always return False. By this we
        # can avoid creating processes.
        mock_is_alive.return_value = False
        mock_send_hb.return_value = None
        mock_join.return_value = None
        mock_start_stores.return_value = None

        # Some of the variables below are needed as parameters for the
        # process_ping function
        self.test_manager._initialise_rabbitmq()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
        body = 'ping'
        properties = pika.spec.BasicProperties()

        # Make the state non-empty to mock the fact that the processes were
        # already created
        self.test_manager._store_process_dict = self.store_process_dict_example

        self.test_manager._process_ping(blocking_channel, method, properties,
                                        body)

        expected_hb = {
            'component_name': self.test_manager.name,
            'running_processes': [],
            'dead_processes': [SYSTEM_STORE_NAME, GITHUB_STORE_NAME,
                               ALERT_STORE_NAME, CONFIG_STORE_NAME,
                               CL_NODE_STORE_NAME, EVM_NODE_STORE_NAME,
                               CL_CONTRACT_STORE_NAME],
            'timestamp': datetime.now().timestamp()
        }
        mock_send_hb.assert_called_once_with(expected_hb)

    @parameterized.expand([
        ([True, True, True, True, True, True, False],),
        ([True, True, True, True, True, False, False],),
        ([True, True, True, True, False, False, False],),
        ([True, True, True, False, False, False, False],),
        ([True, True, False, False, False, False, False],),
        ([True, False, False, False, False, False, False],),
        ([False, False, False, False, False, False, False],),
    ])
    @freeze_time("2012-01-01")
    @mock.patch.object(StoreManager, "_send_heartbeat")
    @mock.patch.object(StoreManager, "_start_stores_processes")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(multiprocessing.Process, "join")
    def test_process_ping_restarts_dead_processes(
            self, is_alive_return, mock_join, mock_is_alive, mock_start_stores,
            mock_send_hb) -> None:
        # We will perform this test by checking that _start_stores_processes is
        # called, as the actual restarting logic was already tested above. Note
        # we wil mock is_alive by setting it to always return False. By this we
        # can avoid creating processes.
        mock_is_alive.side_effect = is_alive_return
        mock_send_hb.return_value = None
        mock_join.return_value = None
        mock_start_stores.return_value = None

        # Some of the variables below are needed as parameters for the
        # process_ping function
        self.test_manager._initialise_rabbitmq()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
        body = 'ping'
        properties = pika.spec.BasicProperties()

        # Make the state non-empty to mock the fact that the processes were
        # already created
        self.test_manager._store_process_dict = self.store_process_dict_example

        self.test_manager._process_ping(blocking_channel, method, properties,
                                        body)

        mock_start_stores.assert_called_once()

    @freeze_time("2012-01-01")
    @mock.patch.object(StoreManager, "_send_heartbeat")
    @mock.patch.object(StoreManager, "_start_stores_processes")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(multiprocessing.Process, "join")
    def test_process_ping_does_not_restart_processes_if_all_alive(
            self, mock_join, mock_is_alive, mock_start_stores,
            mock_send_hb) -> None:
        # We will perform this test by checking that _start_stores_processes is
        # called, as the actual restarting logic was already tested above. Note
        # we wil mock is_alive by setting it to always return True. By this we
        # can avoid creating processes.
        mock_is_alive.return_value = True
        mock_send_hb.return_value = None
        mock_join.return_value = None
        mock_start_stores.return_value = None

        # Some of the variables below are needed as parameters for the
        # process_ping function
        self.test_manager._initialise_rabbitmq()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
        body = 'ping'
        properties = pika.spec.BasicProperties()

        # Make the state non-empty to mock the fact that the processes were
        # already created
        self.test_manager._store_process_dict = self.store_process_dict_example

        self.test_manager._process_ping(blocking_channel, method, properties,
                                        body)

        mock_start_stores.assert_not_called()

    @freeze_time("2012-01-01")
    @mock.patch.object(StoreManager, "_send_heartbeat")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(multiprocessing.Process, "start")
    @mock.patch.object(multiprocessing, 'Process')
    def test_process_ping_does_not_send_hb_if_processing_fails(
            self, mock_process, mock_start, mock_is_alive, mock_send_hb
    ) -> None:
        # We will perform this test by checking that _send_heartbeat is not
        # called. Note we will generate an exception from is_alive
        mock_is_alive.side_effect = self.test_exception
        mock_send_hb.return_value = None
        mock_start.return_value = None
        mock_process.return_value = self.dummy_process1

        # Some of the variables below are needed as parameters for the
        # process_ping function
        self.test_manager._initialise_rabbitmq()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
        body = 'ping'
        properties = pika.spec.BasicProperties()

        # Make the state non-empty to mock the fact that the processes were
        # already created
        self.test_manager._store_process_dict = self.store_process_dict_example

        self.test_manager._process_ping(blocking_channel, method, properties,
                                        body)

        mock_send_hb.assert_not_called()

    @mock.patch.object(StoreManager, "_send_heartbeat")
    def test_proc_ping_send_hb_does_not_raise_msg_not_del_exce_if_hb_not_routed(
            self, mock_send_hb) -> None:
        # This test would fail if a msg not del excep is raised, as it is not
        # caught in the test.
        mock_send_hb.side_effect = MessageWasNotDeliveredException('test')

        # Some of the variables below are needed as parameters for the
        # process_ping function
        self.test_manager._initialise_rabbitmq()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
        body = 'ping'
        properties = pika.spec.BasicProperties()

        try:
            self.test_manager._process_ping(blocking_channel, method,
                                            properties, body)
        except MessageWasNotDeliveredException as e:
            self.fail("Was not expecting {} to be raised.".format(e))

    @parameterized.expand([
        (pika.exceptions.AMQPConnectionError,
         pika.exceptions.AMQPConnectionError('test'),),
        (pika.exceptions.AMQPChannelError,
         pika.exceptions.AMQPChannelError('test'),),
        (Exception, Exception('test'),),
    ])
    @mock.patch.object(StoreManager, "_send_heartbeat")
    def test_process_ping_send_hb_raises_unexpected_error_if_raised(
            self, exception_class, exception_instance,
            mock_send_heartbeat) -> None:
        mock_send_heartbeat.side_effect = exception_instance

        # Some of the variables below are needed as parameters for the
        # process_ping function
        self.test_manager._initialise_rabbitmq()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
        body = 'ping'
        properties = pika.spec.BasicProperties()

        self.assertRaises(exception_class, self.test_manager._process_ping,
                          blocking_channel, method, properties, body)
