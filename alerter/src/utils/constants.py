# Exchanges
CONFIG_EXCHANGE = 'config'
RAW_DATA_EXCHANGE = 'raw_data'
STORE_EXCHANGE = 'store'
ALERT_EXCHANGE = 'alert'
HEALTH_CHECK_EXCHANGE = 'health_check'

# Queues that need to be declared in the run_alerter to avoid configs being sent
# while a component has not started yet. Basically these are all config queues.
ALERT_ROUTER_CONFIGS_QUEUE_NAME = 'alert_router_configs_queue'
SYSTEM_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME = \
    'system_alerters_manager_configs_queue'
CHANNELS_MANAGER_CONFIGS_QUEUE_NAME = 'channels_manager_configs_queue'
GITHUB_MONITORS_MANAGER_CONFIGS_QUEUE_NAME = \
    'github_monitors_manager_configs_queue'
SYSTEM_MONITORS_MANAGER_CONFIGS_QUEUE_NAME = \
    'system_monitors_manager_configs_queue'

RESTART_SLEEPING_PERIOD = 10
RE_INITIALIZE_SLEEPING_PERIOD = 10
