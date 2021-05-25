# CONFIG Folder Identifiers
GENERAL = 'general'
CHAINS = 'chains'
CHANNELS = 'channels'
GLOBAL = 'global'
COSMOS_NODE_CONFIG = 'cosmos_nodes_config'
SUBSTRATE_NODE_CONFIG = 'substrate_nodes_config'
NODES_CONFIG = 'nodes_config'
REPOS_CONFIG = 'repos_config'
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
"""
MONITORABLES_PARSING_HELPER = {
    REPOS_CONFIG: [{
        "id": 'id',
        "name_key": 'repo_name',
        "monitor_key": 'monitor_repo',
        "config_key": 'repos'
    }],
    SYSTEMS_CONFIG: [{
        "id": 'id',
        "name_key": 'name',
        "monitor_key": 'monitor_system',
        "config_key": 'systems'
    }],
    COSMOS_NODE_CONFIG: [{
        "id": 'id',
        "name_key": 'name',
        "monitor_key": 'monitor_system',
        "config_key": 'systems'
    }],
    SUBSTRATE_NODE_CONFIG: [{
        "id": 'id',
        "name_key": 'name',
        "monitor_key": 'monitor_system',
        "config_key": 'systems'
    }]
}
