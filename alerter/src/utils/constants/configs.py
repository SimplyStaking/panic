# CONFIG Folder Identifiers
GENERAL = 'general'
CHAINS = 'chains'
CHANNELS = 'channels'
COSMOS_NODE_CONFIG = 'cosmos_nodes_config'
SUBSTRATE_NODE_CONFIG = 'substrate_nodes_config'
CHAINLINK_NODE_CONFIG = 'chainlink_nodes_config'
NODES_CONFIG = 'nodes_config'
GITHUB_REPOS_CONFIG = 'github_repos_config'
SYSTEMS_CONFIG = 'systems_config'
ALERTS_CONFIG = 'alerts_config'
TELEGRAM_CONFIG = 'telegram_config'
EMAIL_CONFIG = 'email_config'
OPSGENIE_CONFIG = 'opsgenie_config'
PAGERDUTY_CONFIG = 'pagerduty_config'
TWILIO_CONFIG = 'twilio_config'

# Helpers to assist with routing key parsing
"""
This configuration object is useful as when COSMOS and SUBSTRATE nodes
are added, they will have multiple monitorable sources and not just
systems, therefore by storing them in a list and iterating through
the dictionaries it is easier to bundle up the list of monitorable
data.

In the below, the master_monitor_key is the key such that if False it will 
always deem a monitorable as not being monitored. In addition to this, if the
master_monitor_key is True, a monitorable is said to be monitored if at least 
one of the elements contained in sub_monitor_keys is True. If sub_monitor_keys
is None, the sub_monitor_keys are ignored, and thus a monitorable is said to be
monitored if master_monitor_key is True only. Note that this had to be done 
because multiple monitor_keys could be associated with the same config_key.
"""

# TODO: Reflect the last paragraph above in the user of this function.
MONITORABLES_PARSING_HELPER = {
    GITHUB_REPOS_CONFIG: [{
        "id": 'id',
        "name_key": 'repo_name',
        "master_monitor_key": 'monitor_repo',
        "sub_monitor_keys": None,
        "config_key": 'github_repos'
    }],
    SYSTEMS_CONFIG: [{
        "id": 'id',
        "name_key": 'name',
        "master_monitor_key": 'monitor_system',
        "sub_monitor_keys": None,
        "config_key": 'systems'
    }],
    COSMOS_NODE_CONFIG: [{
        "id": 'id',
        "name_key": 'name',
        "master_monitor_key": 'monitor_system',
        "sub_monitor_keys": None,
        "config_key": 'systems'
    }],
    SUBSTRATE_NODE_CONFIG: [{
        "id": 'id',
        "name_key": 'name',
        "master_monitor_key": 'monitor_system',
        "sub_monitor_keys": None,
        "config_key": 'systems'
    }],
    CHAINLINK_NODE_CONFIG: [{
        "id": 'id',
        "name_key": 'name',
        "master_monitor_key": 'monitor_node',
        "sub_monitor_keys": ['monitor_prometheus'],
        "config_key": 'nodes'
    }]
}
