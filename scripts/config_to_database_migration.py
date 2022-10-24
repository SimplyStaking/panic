import configparser
import copy
import json
import os
import bson
import pymongo
from datetime import datetime

COSMOS_NODE_FIELDS = [('parent_id', 'str'), ('name', 'str'),
                      ('cosmos_rest_url', 'str'),
                      ('monitor_cosmos_rest', 'bool'),
                      ('prometheus_url', 'str'), ('monitor_prometheus', 'bool'),
                      ('exporter_url', 'str'), ('monitor_system', 'bool'),
                      ('is_validator', 'bool'), ('monitor_node', 'bool'),
                      ('is_archive_node', 'bool'),
                      ('use_as_data_source', 'bool'),
                      ('monitor_network', 'bool'),
                      ('operator_address', 'str'),
                      ('monitor_tendermint_rpc', 'bool'),
                      ('tendermint_rpc_url', 'str')]
CHAINLINK_NODE_FIELDS = [('parent_id', 'str'), ('name', 'str'),
                         ('node_prometheus_urls', 'str'),
                         ('monitor_prometheus', 'bool'),
                         ('monitor_node', 'bool'), ('evm_nodes_urls', 'str'),
                         ('weiwatchers_url', 'str'),
                         ('monitor_contracts', 'bool')]
SUBSTRATE_NODE_FIELDS = [('parent_id', 'str'), ('name', 'str'),
                         ('node_ws_url', 'str'), ('exporter_url', 'str'),
                         ('monitor_system', 'bool'), ('is_validator', 'bool'),
                         ('monitor_node', 'bool'), ('is_archive_node', 'bool'),
                         ('use_as_data_source', 'bool'),
                         ('stash_address', 'str'),
                         ('governance_addresses', 'str'),
                         ('monitor_network', 'bool')]
NODE_FIELDS = {
    'cosmos': COSMOS_NODE_FIELDS,
    'chainlink': CHAINLINK_NODE_FIELDS,
    'substrate': SUBSTRATE_NODE_FIELDS
}

NODE_FIELDS_COMBINED = (
        COSMOS_NODE_FIELDS + CHAINLINK_NODE_FIELDS + SUBSTRATE_NODE_FIELDS
)

EVM_NODE_FIELDS = [('parent_id', 'str'), ('name', 'str'),
                   ('node_http_url', 'str'), ('monitor_node', 'bool')]
SYSTEMS_FIELDS = [('parent_id', 'str'), ('name', 'str'),
                  ('exporter_url', 'str'), ('monitor_system', 'bool')]
WEIWATCHERS_FIELDS = [('name', 'str'), ('parent_id', 'str'),
                      ('weiwatchers_url', 'str'), ('monitor_contracts', 'bool')]
GITHUB_REPOS_FIELDS = [('parent_id', 'str'), ('repo_name', 'str'),
                       ('monitor_repo', 'bool')]
DOCKERHUB_REPOS_FIELDS = [('parent_id', 'str'), ('repo_name', 'str'),
                          ('repo_namespace', 'str'), ('monitor_repo', 'bool')]
THRESHOLD_ALERT_FIELDS = [('name', 'str'), ('parent_id', 'str'),
                          ('enabled', 'bool'), ('warning_threshold', 'int'),
                          ('warning_enabled', 'bool'),
                          ('critical_threshold', 'int'),
                          ('critical_repeat', 'int'),
                          ('critical_repeat_enabled', 'bool'),
                          ('critical_enabled', 'bool')]
TIME_WINDOW_ALERT_FIELDS = [('name', 'str'), ('parent_id', 'str'),
                            ('enabled', 'bool'), ('warning_threshold', 'int'),
                            ('warning_time_window', 'int'),
                            ('warning_enabled', 'bool'),
                            ('critical_threshold', 'int'),
                            ('critical_time_window', 'int'),
                            ('critical_repeat', 'int'),
                            ('critical_repeat_enabled', 'bool'),
                            ('critical_enabled', 'bool')]
SEVERITY_ALERT_FIELDS = [('name', 'str'), ('parent_id', 'str'),
                         ('enabled', 'bool'), ('severity', 'str')]

OPSGENIE_FIELDS = [('channel_name', 'str'), ('api_token', 'str'),
                   ('eu', 'bool'), ('info', 'bool'), ('warning', 'bool'),
                   ('critical', 'bool'), ('error', 'bool'),
                   ('parent_ids', 'str'), ('parent_names', 'str')]

SLACK_FIELDS = [('channel_name', 'str'), ('bot_token', 'str'),
                ('app_token', 'str'), ('bot_channel_id', 'str'),
                ('info', 'bool'), ('warning', 'bool'), ('critical', 'bool'),
                ('error', 'bool'), ('alerts', 'bool'), ('commands', 'bool'),
                ('parent_ids', 'str'), ('parent_names', 'str')]

TELEGRAM_FIELDS = [('channel_name', 'str'), ('bot_token', 'str'),
                   ('chat_id', 'str'), ('info', 'bool'), ('warning', 'bool'),
                   ('critical', 'bool'), ('error', 'bool'), ('alerts', 'bool'),
                   ('commands', 'bool'), ('parent_ids', 'str'),
                   ('parent_names', 'str')]

TWILIO_FIELDS = [('channel_name', 'str'), ('account_sid', 'str'),
                 ('auth_token', 'str'), ('twilio_phone_no', 'str'),
                 ('twilio_phone_numbers_to_dial_valid', 'list'),
                 ('parent_ids', 'str'), ('parent_names', 'str')]

EMAIL_FIELDS = [('channel_name', 'str'), ('port', 'int'), ('smtp', 'str'),
                ('email_from', 'str'), ('emails_to', 'list'),
                ('username', 'str'), ('password', 'str'), ('info', 'bool'),
                ('warning', 'bool'), ('critical', 'bool'), ('error', 'bool'),
                ('parent_ids', 'str'), ('parent_names', 'str')]

PAGERDUTY_FIELDS = [('channel_name', 'str'), ('integration_key', 'str'),
                    ('info', 'bool'), ('warning', 'bool'), ('critical', 'bool'),
                    ('error', 'bool'), ('parent_ids', 'str'),
                    ('parent_names', 'str')]

CHANNEL_FIELDS = {
    'opsgenie': OPSGENIE_FIELDS,
    'slack': SLACK_FIELDS,
    'telegram': TELEGRAM_FIELDS,
    'twilio': TWILIO_FIELDS,
    'email': EMAIL_FIELDS,
    'pagerduty': PAGERDUTY_FIELDS,
}

CHANNEL_FIELDS_COMBINED = (OPSGENIE_FIELDS + SLACK_FIELDS + TELEGRAM_FIELDS) + (
        TWILIO_FIELDS + EMAIL_FIELDS + PAGERDUTY_FIELDS)

subchain_old_new_ids = {}


def load_api_data_from_json(path):
    with open(f'../api/base/dump/{path}') as file:
        return json.loads(file.read())


def load_generic_api_data_from_jsons():
    base_chains = load_api_data_from_json('base_chains.json')
    generics = load_api_data_from_json('generics.json')

    return base_chains + generics


def load_alerts_api_data_from_jsons():
    threshold_alerts = load_api_data_from_json('threshold_alert.json')
    severity_alerts = load_api_data_from_json('severity_alerts.json')
    time_window_alerts = load_api_data_from_json('time_window_alert.json')

    return [threshold_alerts, severity_alerts, time_window_alerts]


def get_generic_api_ids():
    generic_data = load_generic_api_data_from_jsons()

    data = {}
    for generic_data_type in generic_data:
        data[generic_data_type['value']] = bson.ObjectId(
            generic_data_type['_id'])

    return data


def update_dict(key, data, dict_to_update):
    field = key[0]
    if field in data:
        dict_to_update[field] = data[field]
    else:
        dict_to_update[field] = None


def generate_mongo_subchain_config(base_chain_type, sub_chain, contract, nodes,
                                   evm_nodes, systems, github_repos,
                                   dockerhub_repos, threshold_alerts,
                                   severity_alerts, time_window_alerts):
    generic_types_ids = get_generic_api_ids()
    (threshold_alert_data, severity_alert_data,
     time_window_alert_data) = load_alerts_api_data_from_jsons()

    config_id = bson.objectid.ObjectId()
    subchain_old_new_ids[sub_chain] = config_id

    mongo_config = {}
    date_time_now = datetime.now()

    mongo_config['_id'] = config_id
    mongo_config['status'] = True
    mongo_config['created'] = date_time_now
    mongo_config['modified'] = None
    mongo_config['ready'] = True

    mongo_config['base_chain'] = generic_types_ids[base_chain_type.lower()]

    mongo_config['sub_chain'] = {
        '_id': bson.objectid.ObjectId(),
        'name': sub_chain,
        'status': True,
        'created': date_time_now,
        'modified': None
    }

    mongo_config['contract'] = None
    if contract:
        key = list(contract.keys())[0]
        mongo_config['contract'] = {
            '_id': bson.objectid.ObjectId(),
            'created': date_time_now,
            'status': True,
            'modified': None,
            'url': contract[key]['weiwatchers_url'],
            'monitor': contract[key]['monitor_contracts'],
            'name': contract[key]['name'],
        }

    mongo_config['nodes'] = []
    if nodes:
        for node_id, node_data in nodes.items():
            node_object = {
                '_id': bson.objectid.ObjectId(),
                'created': date_time_now,
                'status': True,
                'modified': None
            }
            for node_field in NODE_FIELDS_COMBINED:
                update_dict(node_field, node_data, node_object)
            del node_object['parent_id']
            mongo_config['nodes'].append(node_object)

    mongo_config['evm_nodes'] = []
    if evm_nodes:
        for evm_node_id, evm_node_data in evm_nodes.items():
            evm_node_object = {
                '_id': bson.objectid.ObjectId(),
                'created': date_time_now,
                'status': True,
                'modified': None
            }
            for evm_node_field in EVM_NODE_FIELDS:
                update_dict(evm_node_field, evm_node_data, evm_node_object)
            evm_node_object['monitor'] = evm_node_object['monitor_node']
            del evm_node_object['monitor_node']
            del evm_node_object['parent_id']
            mongo_config['evm_nodes'].append(evm_node_object)

    mongo_config['systems'] = []
    if systems:
        for systems_id, systems_data in systems.items():
            systems_object = {
                '_id': bson.objectid.ObjectId(),
                'created': date_time_now,
                'status': True,
                'modified': None
            }
            for systems_field in SYSTEMS_FIELDS:
                update_dict(systems_field, systems_data, systems_object)
            systems_object['monitor'] = systems_object['monitor_system']
            del systems_object['monitor_system']
            del systems_object['parent_id']
            mongo_config['systems'].append(systems_object)

    mongo_config['repositories'] = []
    if github_repos:
        for repo_id, repo_data in github_repos.items():
            repo_object = {
                '_id': bson.objectid.ObjectId(),
                'created': date_time_now,
                'status': True,
                'modified': None
            }
            for repo_field in GITHUB_REPOS_FIELDS:
                update_dict(repo_field, repo_data, repo_object)
                        
            repo_object['value'] = None
            repo_object['namespace'] = None
            repo_object['monitor'] = repo_object['monitor_repo']
            del repo_object['monitor_repo']
            repo_object['name'] = repo_object['repo_name']
            del repo_object['repo_name']
            repo_object['type'] = generic_types_ids['github']
            del repo_object['parent_id']
            mongo_config['repositories'].append(repo_object)
    if dockerhub_repos:
        for repo_id, repo_data in dockerhub_repos.items():
            repo_object = {
                '_id': bson.objectid.ObjectId(),
                'created': date_time_now,
                'status': True,
                'modified': None
            }
            for repo_field in DOCKERHUB_REPOS_FIELDS:
                update_dict(repo_field, repo_data, repo_object)
            
            repo_object['value'] = None
            repo_object['monitor'] = repo_object['monitor_repo']
            del repo_object['monitor_repo']
            repo_object['name'] = repo_object['repo_name']
            del repo_object['repo_name']
            repo_object['namespace'] = repo_object['repo_namespace']
            del repo_object['repo_namespace']
            repo_object['type'] = generic_types_ids['dockerhub']
            del repo_object['parent_id']
            mongo_config['repositories'].append(repo_object)

    mongo_config['threshold_alerts'] = []
    for _, threshold_alert in threshold_alerts.items():
        threshold_alert_object = next(
            alert for alert in threshold_alert_data if alert[
                'value'] == threshold_alert['name'])

        threshold_alert_object['_id'] = bson.ObjectId(
            threshold_alert_object['_id'])
        if threshold_alerts:
            threshold_alert_object['created'] = date_time_now
            threshold_alert_object['modified'] = None
            threshold_alert_object['enabled'] = threshold_alert['enabled']
            threshold_alert_object['warning']['enabled'] = threshold_alert[
                'warning_enabled']
            threshold_alert_object['warning']['threshold'] = threshold_alert[
                'warning_threshold']
            threshold_alert_object['critical']['enabled'] = threshold_alert[
                'critical_enabled']
            threshold_alert_object['critical']['threshold'] = threshold_alert[
                'critical_threshold']
            threshold_alert_object['critical']['repeat'] = threshold_alert[
                'critical_repeat']
            threshold_alert_object['critical'][
                'repeat_enabled'] = threshold_alert['critical_repeat_enabled']
        mongo_config['threshold_alerts'].append(threshold_alert_object)

    mongo_config['severity_alerts'] = []
    for _, severity_alert in severity_alerts.items():
        severity_alert_object = next(
            alert for alert in severity_alert_data if alert[
                'value'] == severity_alert['name'])

        severity_alert_object['_id'] = bson.ObjectId(
            severity_alert_object['_id'])
        if severity_alerts:
            severity_alert_object['created'] = date_time_now
            severity_alert_object['modified'] = None
            severity_alert_object['enabled'] = severity_alert['enabled']
            severity_alert_object['type'] = generic_types_ids[
                severity_alert['severity'].lower()]
        mongo_config['severity_alerts'].append(severity_alert_object)

    mongo_config['time_window_alerts'] = []
    for _, time_window_alert in time_window_alerts.items():
        time_window_alert_object = next(
            alert for alert in time_window_alert_data if alert[
                'value'] == time_window_alert['name'])

        time_window_alert_object['_id'] = bson.ObjectId(
            time_window_alert_object['_id'])
        if time_window_alerts:
            time_window_alert_object['created'] = date_time_now
            time_window_alert_object['modified'] = None
            time_window_alert_object['enabled'] = time_window_alert['enabled']
            time_window_alert_object['warning']['enabled'] = time_window_alert[
                'warning_enabled']
            time_window_alert_object['warning'][
                'threshold'] = time_window_alert['warning_threshold']
            time_window_alert_object['warning'][
                'time_window'] = time_window_alert['warning_time_window']
            time_window_alert_object['critical']['enabled'] = time_window_alert[
                'critical_enabled']
            time_window_alert_object['critical'][
                'threshold'] = time_window_alert['critical_threshold']
            time_window_alert_object['critical']['repeat'] = time_window_alert[
                'critical_repeat']
            time_window_alert_object['critical'][
                'repeat_enabled'] = time_window_alert['critical_repeat_enabled']
            time_window_alert_object['critical'][
                'time_window'] = time_window_alert['critical_time_window']
        mongo_config['time_window_alerts'].append(time_window_alert_object)

    mongo_config['config_type'] = generic_types_ids['sub_chain']

    return mongo_config


def generate_mongo_channel_config(channel_config, channel_type):
    generic_types_ids = get_generic_api_ids()
    date_time_now = datetime.now()
    mongo_config = {
        'created': date_time_now,
        'modified': None,
        'configs': []
    }

    for field, value in channel_config.items():
        mongo_config[field] = value

    mongo_config['name'] = mongo_config['channel_name']
    del mongo_config['channel_name']

    if channel_type == 'twilio':
        mongo_config['twilio_phone_numbers_to_dial'] = mongo_config[
            'twilio_phone_numbers_to_dial_valid']
        del mongo_config['twilio_phone_numbers_to_dial_valid']

        mongo_config['twilio_phone_number'] = mongo_config['twilio_phone_no']
        del mongo_config['twilio_phone_no']

    associated_chains = channel_config['parent_names'].split(',')
    if '' in associated_chains:
        associated_chains.remove('')
    if len(associated_chains) > 0:
        for chain in associated_chains:
            mongo_config['configs'].append(subchain_old_new_ids[chain])
    del mongo_config['parent_names']
    del mongo_config['parent_ids']

    mongo_config['type'] = generic_types_ids[channel_type]
    mongo_config['config_type'] = generic_types_ids[f'{channel_type}_channel']

    return mongo_config


def get_data_and_parse(config, fields):
    data = {}

    if len(config.sections()) > 0:
        for section in config.sections():
            data[section] = {}
            for field in fields:
                key = field[0]
                data_type = field[1]
                try:
                    if data_type == 'bool':
                        data[section][key] = config[section][key] == 'true'
                    elif data_type == 'int':
                        data[section][key] = int(config[section][key])
                    elif data_type == 'list':
                        data[section][key] = config[section][key].split(',')
                    else:
                        data[section][key] = config[section][key]
                except KeyError:
                    data[section][key] = ''

    return data


def get_severity_alerts_from_config(config):
    config = copy.deepcopy(config)
    for section in config.sections():
        keys = [key for key, _ in config.items(section)]
        if 'warning_threshold' in keys:
            config.remove_section(section)
    return config


def get_time_window_alerts_from_config(config):
    config = copy.deepcopy(config)
    for section in config.sections():
        keys = [key for key, _ in config.items(section)]
        if 'warning_time_window' not in keys:
            config.remove_section(section)

    return config


def get_threshold_alerts_from_config(config):
    config = copy.deepcopy(config)
    for section in config.sections():
        keys = [key for key, _ in config.items(section)]
        if 'severity' in keys or 'warning_time_window' in keys:
            config.remove_section(section)

    return config


def get_config_parser(path):
    config_parser = configparser.ConfigParser()
    config_parser.read(path)

    return config_parser


def process_config(base_chain_name, sub_chain):
    if base_chain_name == 'GENERAL':
        chain_name = 'GENERAL'
    else:
        chain_name = sub_chain.name
    node_config = None
    evm_node_config = None
    systems_config = None
    weiwatchers_config = None
    github_repos_config = None
    dockerhub_repos_config = None
    threshold_alerts_config = None
    time_window_alerts_config = None
    severity_alerts_config = None
    for file in os.scandir(sub_chain):
        if base_chain_name == 'GENERAL':
            full_path = f'{sub_chain}/{file.name}'
        else:
            full_path = f'{sub_chain.path}/{file.name}'
        config_parser = get_config_parser(full_path)
        if file.name == 'nodes_config.ini':
            node_config = get_data_and_parse(config_parser,
                                             NODE_FIELDS[base_chain_name])
        if file.name == 'evm_nodes_config.ini':
            evm_node_config = get_data_and_parse(config_parser,
                                                 EVM_NODE_FIELDS)
        if file.name == 'systems_config.ini':
            systems_config = get_data_and_parse(config_parser,
                                                SYSTEMS_FIELDS)
        if file.name == 'weiwatchers_config.ini':
            weiwatchers_config = get_data_and_parse(config_parser,
                                                    WEIWATCHERS_FIELDS)
        if file.name == 'github_repos_config.ini':
            github_repos_config = get_data_and_parse(config_parser,
                                                     GITHUB_REPOS_FIELDS)
        if file.name == 'dockerhub_repos_config.ini':
            dockerhub_repos_config = get_data_and_parse(
                config_parser, DOCKERHUB_REPOS_FIELDS)
        if file.name == 'alerts_config.ini':
            threshold_alerts = get_threshold_alerts_from_config(
                config_parser)
            threshold_alerts_config = get_data_and_parse(
                threshold_alerts, THRESHOLD_ALERT_FIELDS)
            time_window_alerts = \
                get_time_window_alerts_from_config(config_parser)
            time_window_alerts_config = get_data_and_parse(
                time_window_alerts, TIME_WINDOW_ALERT_FIELDS)
            severity_alerts = get_severity_alerts_from_config(
                config_parser)
            severity_alerts_config = get_data_and_parse(
                severity_alerts, SEVERITY_ALERT_FIELDS)

    return generate_mongo_subchain_config(
        base_chain_type=base_chain_name,
        sub_chain=chain_name,
        contract=weiwatchers_config,
        nodes=node_config,
        evm_nodes=evm_node_config,
        systems=systems_config,
        github_repos=github_repos_config,
        dockerhub_repos=dockerhub_repos_config,
        threshold_alerts=threshold_alerts_config,
        severity_alerts=severity_alerts_config,
        time_window_alerts=time_window_alerts_config
    )


def process_base_chain(base_chain_name):
    dir_path = f'../config/chains/{base_chain_name}/'

    if base_chain_name == 'general':
        dir_path = f'../config/{base_chain_name}/'

    if not os.path.isdir(dir_path):
        return

    subchains_to_return = []
    if base_chain_name == 'general':
        subchains_to_return.append(process_config('GENERAL', dir_path))
        return subchains_to_return

    for entry in os.scandir(dir_path):
        if entry.is_dir():
            subchains_to_return.append(process_config(base_chain_name, entry))

    return subchains_to_return


def process_channel_config(channel_file):
    config_parser = get_config_parser(channel_file.path)
    channel_type = channel_file.name.split('_')[0]
    channel_config = get_data_and_parse(config_parser,
                                        CHANNEL_FIELDS[channel_type])

    channel_configs_to_return = []
    for channel_id, channel_data in channel_config.items():
        channel_configs_to_return.append(
            generate_mongo_channel_config(channel_data, channel_type))

    return channel_configs_to_return


def process_channels():
    dir_path = '../config/channels/'
    if not os.path.isdir(dir_path):
        return []

    channels = []
    for channels_config in os.scandir(dir_path):
        channels_processed = process_channel_config(channels_config)
        if channels_processed:
            for channel in channels_processed:
                channels.append(channel)

    return channels


def process_base_chains():
    subchains_to_return = []
    for base_chain in ['chainlink', 'substrate', 'cosmos', 'general']:
        subchains = process_base_chain(base_chain)
        if subchains:
            for subchain in subchains:
                subchains_to_return.append(subchain)

    return subchains_to_return


def update_mongo_db(configs_to_add):
    client = pymongo.MongoClient(
        host=['rs1:27017', 'rs2:27017', 'rs3:27017'],
        replicaSet='replica-set',
        readPreference='primaryPreferred')

    db = client['panicdb']

    col1 = db['configs']
    col2 = db['configs_old']

    # Delete all docs in collection in the case of persistent configs
    col1.delete_many({})
    col2.delete_many({})

    if len(configs_to_add) > 0:
        col1.insert_many(configs_to_add)
        col2.insert_many(configs_to_add)

    print('Configs successfully migrated to MongoDB.')


# def clear_config_directory():
#     shutil.rmtree('.../config')
#     os.mkdir('.../config')
#     f = open('.../config/.gitkeep', 'x')
#     f.close()


def check_if_any_configs_exist():
    if len([f.path for f in os.scandir('../config') if f.is_dir()]) == 0:
        print('No configurations found. Skipping migration process...')
        exit()


if __name__ == "__main__":
    configs = []

    # check_if_any_configs_exist()

    configs += process_base_chains()

    configs += process_channels()

    update_mongo_db(configs)

    # clear_config_directory()

