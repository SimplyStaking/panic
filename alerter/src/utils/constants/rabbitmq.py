# Exchanges
CONFIG_EXCHANGE = 'config'
RAW_DATA_EXCHANGE = 'raw_data'
STORE_EXCHANGE = 'store'
ALERT_EXCHANGE = 'alert'
HEALTH_CHECK_EXCHANGE = 'health_check'
MONITORABLE_EXCHANGE = 'monitorable'

# Exchange Types
TOPIC = 'topic'
DIRECT = 'direct'

# Queues
CONFIGS_MANAGER_HEARTBEAT_QUEUE = "configs_manager_heartbeat_queue"
GH_MON_MAN_HEARTBEAT_QUEUE_NAME = 'github_monitors_manager_heartbeat_queue'
GH_MON_MAN_CONFIGS_QUEUE_NAME = 'github_monitors_manager_configs_queue'
DH_MON_MAN_HEARTBEAT_QUEUE_NAME = 'dockerhub_monitors_manager_heartbeat_queue'
DH_MON_MAN_CONFIGS_QUEUE_NAME = 'dockerhub_monitors_manager_configs_queue'
SYS_MON_MAN_HEARTBEAT_QUEUE_NAME = 'system_monitors_manager_heartbeat_queue'
SYS_MON_MAN_CONFIGS_QUEUE_NAME = 'system_monitors_manager_configs_queue'
NODE_MON_MAN_HEARTBEAT_QUEUE_NAME = 'node_monitors_manager_heartbeat_queue'
NODE_MON_MAN_CONFIGS_QUEUE_NAME = 'node_monitors_manager_configs_queue'
CONTRACT_MON_MAN_HEARTBEAT_QUEUE_NAME = \
    'contract_monitors_manager_heartbeat_queue'
CONTRACT_MON_MAN_CONFIGS_QUEUE_NAME = 'contract_monitors_manager_configs_queue'
NETWORK_MON_MAN_HEARTBEAT_QUEUE_NAME = \
    'network_monitors_manager_heartbeat_queue'
NETWORK_MON_MAN_CONFIGS_QUEUE_NAME = 'network_monitors_manager_configs_queue'
GITHUB_DT_INPUT_QUEUE_NAME = 'github_data_transformer_input_queue'
DOCKERHUB_DT_INPUT_QUEUE_NAME = 'dockerhub_data_transformer_input_queue'
SYSTEM_DT_INPUT_QUEUE_NAME = 'system_data_transformer_input_queue'
CL_NODE_DT_INPUT_QUEUE_NAME = 'chainlink_node_data_transformer_input_queue'
EVM_NODE_DT_INPUT_QUEUE_NAME = 'evm_node_data_transformer_input_queue'
CL_CONTRACTS_DT_INPUT_QUEUE_NAME = \
    'chainlink_contracts_data_transformer_input_queue'
COSMOS_NODE_DT_INPUT_QUEUE_NAME = 'cosmos_node_data_transformer_input_queue'
COSMOS_NETWORK_DT_INPUT_QUEUE_NAME = \
    'cosmos_network_data_transformer_input_queue'
SUBSTRATE_NODE_DT_INPUT_QUEUE_NAME = \
    'substrate_node_data_transformer_input_queue'
SUBSTRATE_NETWORK_DT_INPUT_QUEUE_NAME = \
    'substrate_network_data_transformer_input_queue'
DT_MAN_HEARTBEAT_QUEUE_NAME = 'data_transformers_manager_heartbeat_queue'
SYSTEM_ALERTER_INPUT_CONFIGS_QUEUE_NAME = "system_alerter_input_configs_queue"
GITHUB_ALERTER_INPUT_QUEUE_NAME = 'github_alerter_input_queue'
EVM_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME = \
    'evm_node_alerter_input_configs_queue'
DOCKERHUB_ALERTER_INPUT_QUEUE_NAME = 'dockerhub_alerter_input_queue'
CL_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME = 'cl_node_alerter_input_configs_queue'
CL_CONTRACT_ALERTER_INPUT_CONFIGS_QUEUE_NAME = \
    'cl_contract_alerter_input_configs_queue'
COSMOS_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME = \
    'cosmos_node_alerter_input_configs_queue'
COSMOS_NETWORK_ALERTER_INPUT_CONFIGS_QUEUE_NAME = \
    'cosmos_network_alerter_input_configs_queue'
SUBSTRATE_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME = \
    'substrate_node_alerter_input_configs_queue'
SUBSTRATE_NETWORK_ALERTER_INPUT_CONFIGS_QUEUE_NAME = \
    'substrate_network_alerter_input_configs_queue'
SYS_ALERTERS_MAN_HEARTBEAT_QUEUE_NAME = \
    'system_alerters_manager_heartbeat_queue'
SYS_ALERTERS_MAN_CONFIGS_QUEUE_NAME = 'system_alerters_manager_configs_queue'
GH_ALERTERS_MAN_HEARTBEAT_QUEUE_NAME = 'github_alerters_manager_heartbeat_queue'
DH_ALERTERS_MAN_HEARTBEAT_QUEUE_NAME = \
    'dockerhub_alerters_manager_heartbeat_queue'
ALERT_ROUTER_CONFIGS_QUEUE_NAME = 'alert_router_configs_queue'
ALERT_ROUTER_INPUT_QUEUE_NAME = 'alert_router_input_queue'
ALERT_ROUTER_HEARTBEAT_QUEUE_NAME = 'alert_router_heartbeat_queue'
ALERT_STORE_INPUT_QUEUE_NAME = 'alert_store_input_queue'
MONITORABLE_STORE_INPUT_QUEUE_NAME = 'monitorable_store_input_queue'
GITHUB_STORE_INPUT_QUEUE_NAME = 'github_store_input_queue'
DOCKERHUB_STORE_INPUT_QUEUE_NAME = 'dockerhub_store_input_queue'
SYSTEM_STORE_INPUT_QUEUE_NAME = 'system_store_input_queue'
COSMOS_NODE_STORE_INPUT_QUEUE_NAME = 'cosmos_node_store_input_queue'
COSMOS_NETWORK_STORE_INPUT_QUEUE_NAME = 'cosmos_network_store_input_queue'
CL_NODE_STORE_INPUT_QUEUE_NAME = 'chainlink_node_store_input_queue'
CL_CONTRACT_STORE_INPUT_QUEUE_NAME = 'chainlink_contract_store_input_queue'
EVM_NODE_STORE_INPUT_QUEUE_NAME = 'evm_node_store_input_queue'
SUBSTRATE_NODE_STORE_INPUT_QUEUE_NAME = 'substrate_node_store_input_queue'
SUBSTRATE_NETWORK_STORE_INPUT_QUEUE_NAME = 'substrate_network_store_input_queue'
DATA_STORES_MAN_HEARTBEAT_QUEUE_NAME = 'data_stores_manager_heartbeat_queue'
CHAN_ALERTS_HAN_INPUT_QUEUE_NAME_TEMPLATE = '{}_alerts_handler_input_queue'
CHAN_CMDS_HAN_HB_QUEUE_NAME_TEMPLATE = '{}_commands_handler_heartbeat_queue'
CHANNELS_MANAGER_CONFIGS_QUEUE_NAME = 'channels_manager_configs_queue'
CHANNELS_MANAGER_HEARTBEAT_QUEUE_NAME = 'channels_manager_heartbeat_queue'
HB_HANDLER_HEARTBEAT_QUEUE_NAME = 'heartbeat_handler_heartbeat_queue'
CL_ALERTERS_MAN_HB_QUEUE_NAME = 'chainlink_alerters_manager_heartbeat_queue'
CL_ALERTERS_MAN_CONFIGS_QUEUE_NAME = 'chainlink_alerters_manager_configs_queue'
COSMOS_ALERTERS_MAN_HB_QUEUE_NAME = 'cosmos_alerters_manager_heartbeat_queue'
COSMOS_ALERTERS_MAN_CONFIGS_QUEUE_NAME = 'cosmos_alerters_manager_configs_queue'
EVM_NODE_ALERTER_MAN_HEARTBEAT_QUEUE_NAME = \
    'evm_node_alerter_manager_heartbeat_queue'
EVM_NODE_ALERTER_MAN_CONFIGS_QUEUE_NAME = \
    'evm_node_alerter_manager_configs_queue'
SUBSTRATE_ALERTERS_MAN_HB_QUEUE_NAME = \
    'substrate_alerters_manager_heartbeat_queue'
SUBSTRATE_ALERTERS_MAN_CONFIGS_QUEUE_NAME = \
    'substrate_alerters_manager_configs_queue'

# Routing Keys
SYSTEM_RAW_DATA_ROUTING_KEY = 'system'
CHAINLINK_NODE_RAW_DATA_ROUTING_KEY = 'node.chainlink'
COSMOS_NODE_RAW_DATA_ROUTING_KEY = 'node.cosmos'
SUBSTRATE_NODE_RAW_DATA_ROUTING_KEY = 'node.substrate'
EVM_NODE_RAW_DATA_ROUTING_KEY = 'node.evm'
CHAINLINK_CONTRACTS_RAW_DATA_ROUTING_KEY = 'contracts.chainlink'
COSMOS_NETWORK_RAW_DATA_ROUTING_KEY = 'network.cosmos'
SUBSTRATE_NETWORK_RAW_DATA_ROUTING_KEY = 'network.substrate'
GITHUB_RAW_DATA_ROUTING_KEY = 'github'
DOCKERHUB_RAW_DATA_ROUTING_KEY = 'dockerhub'

GITHUB_TRANSFORMED_DATA_ROUTING_KEY = 'transformed_data.github'
DOCKERHUB_TRANSFORMED_DATA_ROUTING_KEY = 'transformed_data.dockerhub'
SYSTEM_TRANSFORMED_DATA_ROUTING_KEY = 'transformed_data.system'
CL_NODE_TRANSFORMED_DATA_ROUTING_KEY = 'transformed_data.node.chainlink'
COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY = 'transformed_data.node.cosmos'
COSMOS_NETWORK_TRANSFORMED_DATA_ROUTING_KEY = 'transformed_data.network.cosmos'
SUBSTRATE_NODE_TRANSFORMED_DATA_ROUTING_KEY = 'transformed_data.node.substrate'
SUBSTRATE_NETWORK_TRANSFORMED_DATA_ROUTING_KEY = \
    'transformed_data.network.substrate'
EVM_NODE_TRANSFORMED_DATA_ROUTING_KEY = 'transformed_data.node.evm'
CL_CONTRACT_TRANSFORMED_DATA_ROUTING_KEY = 'transformed_data.contract.chainlink'
SYSTEM_ALERT_ROUTING_KEY = 'alert.system'
GITHUB_ALERT_ROUTING_KEY = 'alert.github'
DOCKERHUB_ALERT_ROUTING_KEY = 'alert.dockerhub'
CL_NODE_ALERT_ROUTING_KEY = 'alert.node.chainlink'
CL_CONTRACT_ALERT_ROUTING_KEY = 'alert.contract.chainlink'
COSMOS_NODE_ALERT_ROUTING_KEY = 'alert.node.cosmos'
COSMOS_NETWORK_ALERT_ROUTING_KEY = 'alert.network.cosmos'
SUBSTRATE_NODE_ALERT_ROUTING_KEY = 'alert.node.substrate'
SUBSTRATE_NETWORK_ALERT_ROUTING_KEY = 'alert.network.substrate'
EVM_NODE_ALERT_ROUTING_KEY = 'alert.node.evm'

ALERT_ROUTER_INPUT_ROUTING_KEY = 'alert.#'
ALERT_STORE_INPUT_ROUTING_KEY = 'alert'
MONITORABLE_STORE_INPUT_ROUTING_KEY = '*.*'
CHANNEL_HANDLER_INPUT_ROUTING_KEY_TEMPLATE = 'channel.{}'
LOG_HANDLER_INPUT_ROUTING_KEY = 'channel.log'
PING_ROUTING_KEY = 'ping'
HEARTBEAT_INPUT_ROUTING_KEY = 'heartbeat.*'
HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY = 'heartbeat.worker'
HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY = 'heartbeat.manager'

### Channels Routing keys
CHANNELS_MANAGER_CONFIGS_ROUTING_KEY = 'channels.*'
ALERT_ROUTER_CONFIGS_ROUTING_KEY = 'channels.*'
CONSOLE_HANDLER_INPUT_ROUTING_KEY = "channel.console"

### Chains Routing keys
GH_MON_MAN_CONFIGS_ROUTING_KEY_CHAINS = 'chains.*.*.github_repos_config'
DH_MON_MAN_CONFIGS_ROUTING_KEY_CHAINS = 'chains.*.*.dockerhub_repos_config'
SYS_MON_MAN_CONFIGS_ROUTING_KEY_CHAINS_SYS = 'chains.*.*.systems_config'
NODES_CONFIGS_ROUTING_KEY_CHAINS = 'chains.*.*.nodes_config'
ALERTS_CONFIGS_ROUTING_KEY_CHAIN = 'chains.*.*.alerts_config'
EVM_NODES_CONFIGS_ROUTING_KEY_CHAINS = 'chains.*.*.evm_nodes_config'

CL_ALERTS_CONFIGS_ROUTING_KEY = 'chains.chainlink.*.alerts_config'
EVM_ALERTS_CONFIGS_ROUTING_KEY = 'chains.chainlink.*.alerts_config'
COSMOS_ALERTS_CONFIGS_ROUTING_KEY = 'chains.cosmos.*.alerts_config'
SUBSTRATE_ALERTS_CONFIGS_ROUTING_KEY = 'chains.substrate.*.alerts_config'


### General Routing keys
GH_MON_MAN_CONFIGS_ROUTING_KEY_GEN = 'general.github_repos_config'
DH_MON_MAN_CONFIGS_ROUTING_KEY_GEN = 'general.dockerhub_repos_config'
SYS_MON_MAN_CONFIGS_ROUTING_KEY_GEN = 'general.systems_config'
ALERTS_CONFIGS_ROUTING_KEY_GEN = 'general.alerts_config'
