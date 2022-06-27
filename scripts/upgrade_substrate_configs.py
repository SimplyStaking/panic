import configparser
import os

config = configparser.ConfigParser()
new_alerts_config = configparser.ConfigParser()
SUBSTRATE_DIR = 'config/chains/substrate'

NODES_INI = 'nodes_config.ini'
NODES_DEL_FIELDS = ['monitor_ws', 'telemetry_url', 'monitor_telemetry',
                    'prometheus_url', 'monitor_prometheus']
NODES_ADD_FIELDS = {'governance_addresses': '',
                    'monitor_network': 'true'}

ALERTS_INI = 'alerts_config.ini'
THRESHOLD_ALERT = 'threshold'
SEVERITY_ALERT = 'severity'
ALERTS_FIELDS_INFO = [
    {'new_index': '1', 'old_index': '1',
     'name': 'cannot_access_validator',
     'old_name': 'cannot_access_validator',
     'type': THRESHOLD_ALERT,
     'defaults': {'warning_threshold': '0',
                  'warning_enabled': 'true',
                  'critical_threshold': '120',
                  'critical_repeat': '300',
                  'critical_repeat_enabled': 'true',
                  'critical_enabled': 'true'}
     },
    {'new_index': '2', 'old_index': '2',
     'name': 'cannot_access_node',
     'old_name': 'cannot_access_node',
     'type': THRESHOLD_ALERT,
     'defaults': {'warning_threshold': '0',
                  'warning_enabled': 'true',
                  'critical_threshold': '300',
                  'critical_repeat': '600',
                  'critical_repeat_enabled': 'true',
                  'critical_enabled': 'false'}
     },
    {'new_index': '3', 'old_index': '4',
     'name': 'no_change_in_best_block_height_validator',
     'old_name': 'no_change_in_best_block_height',
     'type': THRESHOLD_ALERT,
     'defaults': {'warning_threshold': '180',
                  'warning_enabled': 'true',
                  'critical_threshold': '300',
                  'critical_repeat': '180',
                  'critical_repeat_enabled': 'true',
                  'critical_enabled': 'true'}
     },
    {'new_index': '4', 'old_index': '4',
     'name': 'no_change_in_best_block_height_node',
     'old_name': 'no_change_in_best_block_height',
     'type': THRESHOLD_ALERT,
     'defaults': {'warning_threshold': '180',
                  'warning_enabled': 'true',
                  'critical_threshold': '300',
                  'critical_repeat': '300',
                  'critical_repeat_enabled': 'true',
                  'critical_enabled': 'false'}
     },
    {'new_index': '5', 'old_index': '5',
     'name': 'no_change_in_finalized_block_height_validator',
     'old_name': 'no_change_in_finalized_block_height',
     'type': THRESHOLD_ALERT,
     'defaults': {'warning_threshold': '180',
                  'warning_enabled': 'true',
                  'critical_threshold': '300',
                  'critical_repeat': '180',
                  'critical_repeat_enabled': 'true',
                  'critical_enabled': 'true'}
     },
    {'new_index': '6', 'old_index': '5',
     'name': 'no_change_in_finalized_block_height_node',
     'old_name': 'no_change_in_finalized_block_height',
     'type': THRESHOLD_ALERT,
     'defaults': {'warning_threshold': '180',
                  'warning_enabled': 'true',
                  'critical_threshold': '300',
                  'critical_repeat': '300',
                  'critical_repeat_enabled': 'true',
                  'critical_enabled': 'false'}
     },
    {'new_index': '7', 'old_index': '16',
     'name': 'validator_is_syncing',
     'old_name': 'node_is_syncing',
     'type': THRESHOLD_ALERT,
     'defaults': {'warning_threshold': '50',
                  'warning_enabled': 'true',
                  'critical_threshold': '100',
                  'critical_repeat': '300',
                  'critical_repeat_enabled': 'true',
                  'critical_enabled': 'true'}
     },
    {'new_index': '8', 'old_index': '16',
     'name': 'node_is_syncing',
     'old_name': 'node_is_syncing',
     'type': THRESHOLD_ALERT,
     'defaults': {'warning_threshold': '50',
                  'warning_enabled': 'true',
                  'critical_threshold': '100',
                  'critical_repeat': '300',
                  'critical_repeat_enabled': 'true',
                  'critical_enabled': 'false'}
     },
    {'new_index': '9', 'old_index': None,
     'name': 'no_heartbeat_did_not_author_block',
     'old_name': None,
     'type': THRESHOLD_ALERT,
     'defaults': {'warning_threshold': '1800',
                  'warning_enabled': 'true',
                  'critical_threshold': '2700',
                  'critical_repeat': '300',
                  'critical_repeat_enabled': 'false',
                  'critical_enabled': 'true'}
     },
    {'new_index': '10', 'old_index': None,
     'name': 'payout_not_claimed',
     'old_name': None,
     'type': THRESHOLD_ALERT,
     'defaults': {'warning_threshold': '30',
                  'warning_enabled': 'true',
                  'critical_threshold': '60',
                  'critical_repeat': '1',
                  'critical_repeat_enabled': 'true',
                  'critical_enabled': 'true'}
     },
    {'new_index': '11', 'old_index': '6',
     'name': 'system_is_down',
     'old_name': 'system_is_down',
     'type': THRESHOLD_ALERT,
     'defaults': {'warning_threshold': '0',
                  'warning_enabled': 'true',
                  'critical_threshold': '200',
                  'critical_repeat': '300',
                  'critical_repeat_enabled': 'true',
                  'critical_enabled': 'true'}
     },
    {'new_index': '12', 'old_index': '9',
     'name': 'open_file_descriptors',
     'old_name': 'open_file_descriptors',
     'type': THRESHOLD_ALERT,
     'defaults': {'warning_threshold': '85',
                  'warning_enabled': 'true',
                  'critical_threshold': '95',
                  'critical_repeat': '300',
                  'critical_repeat_enabled': 'true',
                  'critical_enabled': 'true'}
     },
    {'new_index': '13', 'old_index': '10',
     'name': 'system_cpu_usage',
     'old_name': 'system_cpu_usage',
     'type': THRESHOLD_ALERT,
     'defaults': {'warning_threshold': '85',
                  'warning_enabled': 'true',
                  'critical_threshold': '95',
                  'critical_repeat': '300',
                  'critical_repeat_enabled': 'true',
                  'critical_enabled': 'true'}
     },
    {'new_index': '14', 'old_index': '11',
     'name': 'system_storage_usage',
     'old_name': 'system_storage_usage',
     'type': THRESHOLD_ALERT,
     'defaults': {'warning_threshold': '85',
                  'warning_enabled': 'true',
                  'critical_threshold': '95',
                  'critical_repeat': '300',
                  'critical_repeat_enabled': 'true',
                  'critical_enabled': 'true'}
     },
    {'new_index': '15', 'old_index': '12',
     'name': 'system_ram_usage',
     'old_name': 'system_ram_usage',
     'type': THRESHOLD_ALERT,
     'defaults': {'warning_threshold': '85',
                  'warning_enabled': 'true',
                  'critical_threshold': '95',
                  'critical_repeat': '300',
                  'critical_repeat_enabled': 'true',
                  'critical_enabled': 'true'}
     },
    {'new_index': '16', 'old_index': '17',
     'name': 'not_active_in_session',
     'old_name': 'validator_not_active_in_session',
     'type': SEVERITY_ALERT,
     'defaults': {'severity': 'WARNING'}
     },
    {'new_index': '17', 'old_index': '36',
     'name': 'is_disabled',
     'old_name': 'validator_is_disabled',
     'type': SEVERITY_ALERT,
     'defaults': {'severity': 'CRITICAL'}
     },
    {'new_index': '18', 'old_index': '35',
     'name': 'not_elected',
     'old_name': 'validator_not_elected',
     'type': SEVERITY_ALERT,
     'defaults': {'severity': 'WARNING'}
     },
    {'new_index': '19', 'old_index': None,
     'name': 'bonded_amount_change',
     'old_name': None,
     'type': SEVERITY_ALERT,
     'defaults': {'severity': 'INFO'}
     },
    {'new_index': '20', 'old_index': '20',
     'name': 'offline',
     'old_name': 'validator_declared_offline',
     'type': SEVERITY_ALERT,
     'defaults': {'severity': 'CRITICAL'}
     },
    {'new_index': '21', 'old_index': '15',
     'name': 'slashed',
     'old_name': 'slashed',
     'type': SEVERITY_ALERT,
     'defaults': {'severity': 'CRITICAL'}
     },
    {'new_index': '22', 'old_index': None,
     'name': 'controller_address_change',
     'old_name': None,
     'type': SEVERITY_ALERT,
     'defaults': {'severity': 'WARNING'}
     },
    {'new_index': '23', 'old_index': None,
     'name': 'grandpa_is_stalled',
     'old_name': None,
     'type': SEVERITY_ALERT,
     'defaults': {'severity': 'WARNING'}
     },
    {'new_index': '24', 'old_index': None,
     'name': 'new_proposal',
     'old_name': None,
     'type': SEVERITY_ALERT,
     'defaults': {'severity': 'INFO'}
     },
    {'new_index': '25', 'old_index': '42',
     'name': 'new_referendum',
     'old_name': 'new_referendum',
     'type': SEVERITY_ALERT,
     'defaults': {'severity': 'INFO'}
     },
    {'new_index': '26', 'old_index': '43',
     'name': 'referendum_concluded',
     'old_name': 'referendum_completed',
     'type': SEVERITY_ALERT,
     'defaults': {'severity': 'INFO'}
     }
]

for entry in os.scandir(SUBSTRATE_DIR):
    if entry.is_dir():
        sub_chain = entry.name
        nodes_config = '{}/{}/{}'.format(SUBSTRATE_DIR, sub_chain, NODES_INI)
        alerts_config = '{}/{}/{}'.format(SUBSTRATE_DIR, sub_chain, ALERTS_INI)

        # Nodes Config
        config.read(nodes_config)
        for node in config.sections():
            for field in NODES_DEL_FIELDS:
                if field in config[node]:
                    del config[node][field]
            for field, value in NODES_ADD_FIELDS.items():
                if field not in config[node]:
                    config[node][field] = value

        with open(nodes_config, 'w') as configfile:
            config.write(configfile, False)
        print('Updated', nodes_config)

        # Alerts Config
        config.read(alerts_config)
        parent_id = config['1']['parent_id']

        for field in ALERTS_FIELDS_INFO:
            old_index = field['old_index']
            new_index = field['new_index']
            defaults = field['defaults']

            data = (config[old_index] if
                    old_index and old_index in config
                    else None)
            if data and data['name'] != field['old_name']:
                data = None

            if field['type'] == THRESHOLD_ALERT:
                new_alerts_config[new_index] = {
                    'name': field['name'],
                    'parent_id': parent_id,
                    'enabled': (data['enabled'] if
                                data and 'enabled' in data
                                else 'true'),
                    'warning_threshold': (data['warning_threshold'] if
                                          data and 'warning_threshold' in data
                                          else defaults['warning_threshold']),
                    'warning_enabled': (data['warning_enabled'] if
                                        data and 'warning_enabled' in data
                                        else defaults['warning_enabled']),
                    'critical_threshold': (data['critical_threshold'] if
                                           data and 'critical_threshold' in data
                                           else defaults['critical_threshold']),
                    'critical_repeat': (data['critical_repeat'] if
                                        data and 'critical_repeat' in data
                                        else defaults['critical_repeat']),
                    'critical_repeat_enabled': (
                        data['critical_repeat_enabled'] if
                        data and 'critical_repeat_enabled' in data
                        else defaults['critical_repeat_enabled']),
                    'critical_enabled': (data['critical_enabled'] if
                                         data and 'critical_enabled' in data
                                         else defaults['critical_enabled'])
                }
            else:
                new_alerts_config[new_index] = {
                    'name': field['name'],
                    'parent_id': parent_id,
                    'enabled': (data['enabled'] if
                                data and 'enabled' in data
                                else 'true'),
                    'severity': (data['severity'] if
                                 data and 'severity' in data
                                 else defaults['severity']),
                }

        with open(alerts_config, 'w') as configfile:
            new_alerts_config.write(configfile, False)
        print('Updated', alerts_config)
