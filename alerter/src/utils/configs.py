# These functions assume that config files are given as parameters

from typing import Dict


def get_newly_added_configs(new_config_file: Dict, current_config_file: Dict) \
        -> Dict:
    new_keys_set = set(new_config_file.keys())
    current_keys_set = set(current_config_file.keys())
    added_keys_set = new_keys_set.difference(current_keys_set)
    return {key: new_config_file[key] for key in added_keys_set}


def get_removed_configs(new_config_file: Dict, current_config_file: Dict) \
        -> Dict:
    new_keys_set = set(new_config_file.keys())
    current_keys_set = set(current_config_file.keys())
    removed_keys_set = current_keys_set.difference(new_keys_set)
    return {key: current_config_file[key] for key in removed_keys_set}


# This function assumes that the configs obey the config schemas, and that
# sub-configurations within the config file are given
def config_is_modified(new_config: Dict, old_config: Dict) -> bool:
    for key, value in new_config.items():
        if value != old_config[key]:
            return True
    return False


def get_modified_configs(new_config_file: Dict, current_config_file: Dict) \
        -> Dict:
    removed_configs = get_removed_configs(new_config_file, current_config_file)
    removed_keys_set = set(removed_configs.keys())
    current_keys_set = set(current_config_file.keys())
    retained_keys_set = current_keys_set.difference(removed_keys_set)
    return {key: current_config_file[key] for key in retained_keys_set if
            config_is_modified(new_config_file[key], current_config_file[key])}


def get_non_modified_configs(new_config_file: Dict, current_config_file: Dict) \
        -> Dict:
    removed_configs = get_removed_configs(new_config_file, current_config_file)
    removed_keys_set = set(removed_configs.keys())
    current_keys_set = set(current_config_file.keys())
    retained_keys_set = current_keys_set.difference(removed_keys_set)
    return {key: current_config_file[key] for key in retained_keys_set
            if not config_is_modified(new_config_file[key],
                                      current_config_file[key])}
