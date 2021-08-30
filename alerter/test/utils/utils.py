import json
from time import sleep
from typing import Union
from unittest.mock import Mock

import pika.exceptions

from src.alerter.alert_code import AlertCode
from src.data_store.redis import RedisApi, Keys
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitorables.contracts.v3 import V3EvmContract
from src.monitorables.contracts.v4 import V4EvmContract
from src.monitorables.nodes.chainlink_node import ChainlinkNode
from src.monitorables.nodes.evm_node import EVMNode
from src.monitorables.repo import GitHubRepo
from src.monitorables.system import System


def infinite_fn() -> None:
    while True:
        sleep(10)


def dummy_function(*args, **kwargs):
    return args, kwargs


def dummy_none_function(*args, **kwargs) -> None:
    return None


def assert_not_called_with(mocked_function: Mock, *args, **kwargs):
    try:
        mocked_function.assert_has_calls(*args, **kwargs)
    except AssertionError:
        return
    raise AssertionError(
        'Expected %s to not have been called.' %
        mocked_function._format_mock_call_signature(args, kwargs))


def assign_side_effect_if_not_none_otherwise_return_value(
        mock_object: Mock, side_effect, return_value, check_value) -> Mock:
    if check_value is None:
        mock_object.return_value = return_value
    else:
        mock_object.side_effect = side_effect

    return mock_object


class TestConnection:
    def __init__(
            self, host=None, port=None, virtual_host=None, credentials=None
    ):
        self.host = host
        self.port = port
        self.virtual_host = virtual_host
        self.credentials = credentials

    def __dict__(self):
        return {
            "host": self.host,
            "port": self.port,
            "virtual_host": self.virtual_host,
            "credentials": self.credentials
        }

    def channel(self):
        return True


class DummyAlertCode(AlertCode):
    TEST_ALERT_CODE = 'test_alert_code'


def delete_queue_if_exists(rabbit: RabbitMQApi, queue_name: str) -> None:
    try:
        rabbit.queue_declare(queue_name, passive=True)
        rabbit.queue_purge(queue_name)
        rabbit.queue_delete(queue_name)
    except pika.exceptions.ChannelClosedByBroker:
        rabbit.logger.debug(
            "Queue {} does not exist - don't need to close".format(queue_name))


def delete_exchange_if_exists(rabbit: RabbitMQApi, exchange_name: str) -> None:
    try:
        rabbit.exchange_declare(exchange_name, passive=True)
        rabbit.exchange_delete(exchange_name)
    except pika.exceptions.ChannelClosedByBroker:
        rabbit.logger.debug(
            "Exchange {} does not exist - don't need to close".format(
                exchange_name))


def disconnect_from_rabbit(rabbit: RabbitMQApi, attempts: int = 3) -> None:
    tries = 0

    while tries < attempts:
        try:
            rabbit.disconnect()
            return
        except Exception as e:
            tries += 1
            rabbit.logger.debug("Could not disconnect to rabbit. Attempts so "
                                "far: {}".format(tries))
            rabbit.logger.debug(e)
            if tries >= attempts:
                raise e


def connect_to_rabbit(rabbit: RabbitMQApi, attempts: int = 3) -> None:
    tries = 0

    while tries < attempts:
        try:
            rabbit.connect()
            return
        except Exception as e:
            tries += 1
            rabbit.logger.debug("Could not disconnect to rabbit. Attempts so "
                                "far: {}".format(tries))
            rabbit.logger.debug(e)
            if tries >= attempts:
                raise e


def save_system_to_redis(redis: RedisApi, system: System) -> None:
    redis_hash = Keys.get_hash_parent(system.parent_id)
    system_id = system.system_id
    redis.hset_multiple(redis_hash, {
        Keys.get_system_process_cpu_seconds_total(system_id):
            str(system.process_cpu_seconds_total),
        Keys.get_system_process_memory_usage(system_id):
            str(system.process_memory_usage),
        Keys.get_system_virtual_memory_usage(system_id):
            str(system.virtual_memory_usage),
        Keys.get_system_open_file_descriptors(system_id):
            str(system.open_file_descriptors),
        Keys.get_system_system_cpu_usage(system_id):
            str(system.system_cpu_usage),
        Keys.get_system_system_ram_usage(system_id):
            str(system.system_ram_usage),
        Keys.get_system_system_storage_usage(system_id):
            str(system.system_storage_usage),
        Keys.get_system_network_transmit_bytes_per_second(system_id):
            str(system.network_transmit_bytes_per_second),
        Keys.get_system_network_receive_bytes_per_second(system_id):
            str(system.network_receive_bytes_per_second),
        Keys.get_system_network_transmit_bytes_total(system_id):
            str(system.network_transmit_bytes_total),
        Keys.get_system_network_receive_bytes_total(system_id):
            str(system.network_receive_bytes_total),
        Keys.get_system_disk_io_time_seconds_in_interval(system_id):
            str(system.disk_io_time_seconds_in_interval),
        Keys.get_system_disk_io_time_seconds_total(system_id):
            str(system.disk_io_time_seconds_total),
        Keys.get_system_last_monitored(system_id): str(system.last_monitored),
        Keys.get_system_went_down_at(system_id): str(system.went_down_at),
    })


def save_github_repo_to_redis(redis: RedisApi, github_repo: GitHubRepo) -> None:
    redis_hash = Keys.get_hash_parent(github_repo.parent_id)
    repo_id = github_repo.repo_id
    redis.hset_multiple(redis_hash, {
        Keys.get_github_no_of_releases(repo_id):
            str(github_repo.no_of_releases),
        Keys.get_github_last_monitored(repo_id):
            str(github_repo.last_monitored),
    })


def save_chainlink_node_to_redis(redis: RedisApi,
                                 cl_node: ChainlinkNode) -> None:
    redis_hash = Keys.get_hash_parent(cl_node.parent_id)
    cl_node_id = cl_node.node_id
    redis.hset_multiple(redis_hash, {
        Keys.get_cl_node_went_down_at_prometheus(cl_node_id):
            str(cl_node.went_down_at_prometheus),
        Keys.get_cl_node_current_height(cl_node_id):
            str(cl_node.current_height),
        Keys.get_cl_node_total_block_headers_received(cl_node_id):
            str(cl_node.total_block_headers_received),
        Keys.get_cl_node_no_of_active_jobs(cl_node_id):
            str(cl_node.no_of_active_jobs),
        Keys.get_cl_node_max_pending_tx_delay(cl_node_id):
            str(cl_node.max_pending_tx_delay),
        Keys.get_cl_node_process_start_time_seconds(cl_node_id):
            str(cl_node.process_start_time_seconds),
        Keys.get_cl_node_total_gas_bumps(cl_node_id):
            str(cl_node.total_gas_bumps),
        Keys.get_cl_node_total_gas_bumps_exceeds_limit(cl_node_id):
            str(cl_node.total_gas_bumps_exceeds_limit),
        Keys.get_cl_node_no_of_unconfirmed_txs(cl_node_id):
            str(cl_node.no_of_unconfirmed_txs),
        Keys.get_cl_node_total_errored_job_runs(cl_node_id):
            str(cl_node.total_errored_job_runs),
        Keys.get_cl_node_current_gas_price_info(cl_node_id):
            'None' if cl_node.current_gas_price_info is None else json.dumps(
                cl_node.current_gas_price_info),
        Keys.get_cl_node_eth_balance_info(cl_node_id):
            json.dumps(cl_node.eth_balance_info),
        Keys.get_cl_node_last_prometheus_source_used(cl_node_id):
            str(cl_node.last_prometheus_source_used),
        Keys.get_cl_node_last_monitored_prometheus(cl_node_id):
            str(cl_node.last_monitored_prometheus)
    })


def save_evm_node_to_redis(redis: RedisApi, evm_node: EVMNode) -> None:
    redis_hash = Keys.get_hash_parent(evm_node.parent_id)
    evm_node_id = evm_node.node_id
    redis.hset_multiple(redis_hash, {
        Keys.get_evm_node_went_down_at(evm_node_id): str(evm_node.went_down_at),
        Keys.get_evm_node_current_height(evm_node_id):
            str(evm_node.current_height),
        Keys.get_evm_node_last_monitored(evm_node_id):
            str(evm_node.last_monitored)
    })


def save_evm_contract_to_redis(
        redis: RedisApi,
        evm_contract: Union[V3EvmContract, V4EvmContract]) -> None:
    redis_hash = Keys.get_hash_parent(evm_contract.parent_id)
    node_id = evm_contract.node_id
    proxy_address = evm_contract.proxy_address
    version = evm_contract.version
    payment_key = Keys.get_evm_contract_withdrawable_payment(
        node_id, proxy_address) if version == 3 \
        else Keys.get_evm_contract_owed_payment(node_id, proxy_address)
    payment_value = evm_contract.withdrawable_payment if version == 3 \
        else evm_contract.owed_payment
    redis.hset_multiple(redis_hash, {
        Keys.get_evm_contract_latest_round(node_id, proxy_address):
            str(evm_contract.latest_round),
        Keys.get_evm_contract_latest_answer(node_id, proxy_address):
            str(evm_contract.latest_answer),
        Keys.get_evm_contract_latest_timestamp(node_id, proxy_address):
            str(evm_contract.latest_timestamp),
        Keys.get_evm_contract_answered_in_round(node_id, proxy_address):
            str(evm_contract.answered_in_round),
        payment_key: payment_value,
        Keys.get_evm_contract_historical_rounds(node_id, proxy_address):
            json.dumps(evm_contract.historical_rounds),
        Keys.get_evm_contract_last_monitored(node_id, proxy_address):
            str(evm_contract.last_monitored)
    })
