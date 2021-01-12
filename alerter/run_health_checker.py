import logging
import multiprocessing
import signal
import sys
import time
from types import FrameType

from src.health_checker.manager import HealthCheckerManager
from src.utils import env
from src.utils.constants import RE_INITIALIZE_SLEEPING_PERIOD, \
    RESTART_SLEEPING_PERIOD, HEALTH_CHECKER_MANAGER_NAME
from src.utils.logging import create_logger, log_and_print
from src.utils.starters import get_initialisation_error_message, \
    get_reattempting_message, get_stopped_message


def _initialize_logger(component_display_name: str, component_module_name: str,
                       log_file_template: str) -> logging.Logger:
    # Try initializing the logger until successful. This had to be done
    # separately to avoid instances when the logger creation failed and we
    # attempt to use it.
    while True:
        try:
            new_logger = create_logger(
                log_file_template.format(component_display_name),
                component_module_name, env.LOGGING_LEVEL, rotating=True)
            break
        except Exception as e:
            msg = get_initialisation_error_message(component_display_name, e)
            # Use a dummy logger in this case because we cannot create the
            # manager's logger.
            log_and_print(msg, dummy_logger)
            log_and_print(get_reattempting_message(component_display_name),
                          dummy_logger)
            # sleep before trying again
            time.sleep(RE_INITIALIZE_SLEEPING_PERIOD)

    return new_logger


def _initialize_health_checker_manager() -> HealthCheckerManager:
    manager_display_name = HEALTH_CHECKER_MANAGER_NAME

    health_checker_manager_logger = _initialize_logger(
        manager_display_name, HealthCheckerManager.__name__,
        env.MANAGERS_LOG_FILE_TEMPLATE)

    # Attempt to initialize the health checker manager
    while True:
        try:
            health_checker_manager = HealthCheckerManager(
                health_checker_manager_logger, manager_display_name)
            break
        except Exception as e:
            msg = get_initialisation_error_message(manager_display_name, e)
            log_and_print(msg, health_checker_manager_logger)
            log_and_print(get_reattempting_message(manager_display_name),
                          health_checker_manager_logger)
            # sleep before trying again
            time.sleep(RE_INITIALIZE_SLEEPING_PERIOD)

    return health_checker_manager


def run_health_checker_manager() -> None:
    health_checker_manager = _initialize_health_checker_manager()

    while True:
        try:
            log_and_print("{} started.".format(health_checker_manager),
                          health_checker_manager.logger)
            health_checker_manager.start()
        except Exception as e:
            health_checker_manager.logger.exception(e)
            log_and_print(get_stopped_message(health_checker_manager),
                          health_checker_manager.logger)
            log_and_print("Restarting {} in {} seconds.".format(
                health_checker_manager, RESTART_SLEEPING_PERIOD),
                health_checker_manager.logger)
            time.sleep(RESTART_SLEEPING_PERIOD)


# If termination signals are received, terminate all child process and exit
def on_terminate(signum: int, stack: FrameType) -> None:
    log_and_print("The Health Checker is terminating. All components will be "
                  "stopped gracefully.", dummy_logger)

    log_and_print("Terminating the {}.".format(HEALTH_CHECKER_MANAGER_NAME),
                  dummy_logger)
    health_checker_manager_process.terminate()
    health_checker_manager_process.join()

    log_and_print("The Health Checker process has ended.", dummy_logger)
    sys.exit()


if __name__ == '__main__':
    dummy_logger = logging.getLogger('Dummy')

    # Start the managers in a separate process
    health_checker_manager_process = multiprocessing.Process(
        target=run_health_checker_manager, args=())
    health_checker_manager_process.start()

    signal.signal(signal.SIGTERM, on_terminate)
    signal.signal(signal.SIGINT, on_terminate)
    signal.signal(signal.SIGHUP, on_terminate)

    # If we don't wait for the processes to terminate the root process will
    # exit
    health_checker_manager_process.join()

    log_and_print("The Health Checker process has ended.", dummy_logger)
    sys.stdout.flush()
