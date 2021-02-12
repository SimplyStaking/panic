from time import sleep

from src.alerter.alert_code import AlertCode
from src.data_store.redis import Keys, RedisApi
from src.monitorables.repo import GitHubRepo
from src.monitorables.system import System


def infinite_fn() -> None:
    while True:
        sleep(10)


class DummyAlertCode(AlertCode):
    TEST_ALERT_CODE = 'test_alert_code'


def save_github_repo_to_redis(redis: RedisApi, github_repo: GitHubRepo) -> None:
    redis_hash = Keys.get_hash_parent(github_repo.parent_id)
    repo_id = github_repo.repo_id
    redis.hset_multiple(redis_hash, {
        Keys.get_github_no_of_releases(repo_id): github_repo.no_of_releases,
        Keys.get_github_last_monitored(repo_id): github_repo.last_monitored,
    })


def save_system_to_redis(redis: RedisApi, system: System) -> None:
    redis_hash = Keys.get_hash_parent(system.parent_id)
    system_id = system.system_id
    redis.hset_multiple(redis_hash, {
        Keys.get_system_process_cpu_seconds_total(system_id):
            system.process_cpu_seconds_total,
        Keys.get_system_process_memory_usage(system_id):
            system.process_memory_usage,
        Keys.get_system_virtual_memory_usage(system_id):
            system.virtual_memory_usage,
        Keys.get_system_open_file_descriptors(system_id):
            system.open_file_descriptors,
        Keys.get_system_system_cpu_usage(system_id):
            system.system_cpu_usage,
        Keys.get_system_system_ram_usage(system_id):
            system.system_ram_usage,
        Keys.get_system_system_storage_usage(system_id):
            system.system_storage_usage,
        Keys.get_system_network_transmit_bytes_per_second(system_id):
            system.network_transmit_bytes_per_second,
        Keys.get_system_network_receive_bytes_per_second(system_id):
            system.network_receive_bytes_per_second,
        Keys.get_system_network_transmit_bytes_total(system_id):
            system.network_transmit_bytes_total,
        Keys.get_system_network_receive_bytes_total(system_id):
            system.network_receive_bytes_total,
        Keys.get_system_disk_io_time_seconds_in_interval(system_id):
            system.disk_io_time_seconds_in_interval,
        Keys.get_system_disk_io_time_seconds_total(system_id):
            system.disk_io_time_seconds_total,
        Keys.get_system_last_monitored(system_id): system.last_monitored,
        Keys.get_system_went_down_at(system_id): system.went_down_at,
    })
