const ConfigParser = require('configparser');
const fs = require('fs');
const path = require('path');
const errors = require('./errors');

// Channel configs and config locations
const USER_CONFIG_TELEGRAM = 'user_config_telegram.ini';
const USER_CONFIG_EMAIL = 'user_config_email.ini';
const USER_CONFIG_TWILIO = 'user_config_twilio.ini';
const USER_CONFIG_PAGERDUTY = 'user_config_pagerduty.ini';
const USER_CONFIG_OPSGENIE = 'user_config_opsgenie.ini';
const ALL_CHANNELS_CONFIG_FILES = [
  USER_CONFIG_TELEGRAM, USER_CONFIG_EMAIL, USER_CONFIG_TWILIO,
  USER_CONFIG_PAGERDUTY, USER_CONFIG_OPSGENIE,
];
const CHANNELS_CONFIGS_LOCATION = path.join('config', 'channels');

// Chain configs and config locations
const USER_CONFIG_NODES = 'user_config_nodes.ini';
const USER_CONFIG_REPOS = 'user_config_repos.ini';
const USER_CONFIG_KMS = 'user_config_kms.ini';
const USER_CONFIG_CHANNELS = 'user_config_channels.ini';
const USER_CONFIG_ALERTS = 'user_config_alerts.ini';
const ALL_CHAINS_CONFIG_FILES = [
  USER_CONFIG_NODES, USER_CONFIG_REPOS, USER_CONFIG_KMS, USER_CONFIG_CHANNELS,
  USER_CONFIG_ALERTS,
];
const COSMOS_CHAINS_CONFIGS_LOCATION = path.join('config', 'chains', 'cosmos');
const SUBSTRATE_CHAINS_CONFIGS_LOCATION = path.join(
  'config', 'chains', 'substrate',
);

// Other configs and config locations
const USER_CONFIG_SYSTEM = 'user_config_systems.ini';
const ALL_OTHER_CONFIG_FILES = [USER_CONFIG_SYSTEM, USER_CONFIG_ALERTS];
const OTHER_CONFIGS_LOCATION = path.join('config', 'others');

// Gets the full path of the config with the name of the config included. This
// method restricts writing and reading from specific locations (adds security).
function getConfigPath(configType, file, chainName = null, baseChain = null) {
  // Determine the full path according to the config type, chainName and
  // baseChain (Only if configType = Chain)
  switch (configType.toLowerCase()) {
    case 'channel':
      return path.join(CHANNELS_CONFIGS_LOCATION, file);
    case 'chain':
      if (baseChain.toLowerCase() === 'cosmos') {
        return path.join(COSMOS_CHAINS_CONFIGS_LOCATION, chainName, file);
      }
      if (baseChain.toLowerCase() === 'substrate') {
        return path.join(SUBSTRATE_CHAINS_CONFIGS_LOCATION, chainName, file);
      }
      throw new errors.InvalidBaseChain();
    case 'other':
      return path.join(OTHER_CONFIGS_LOCATION, file);
    default:
      throw new errors.InvalidConfigType();
  }
}

// Get the config file location. This function expects the full config path
function getConfigLocation(configPath) {
  return configPath.replace(/[^\/]*$/, '');
}

// This function returns true if 'file' is expected in the inferred location
function fileValid(configType, file) {
  switch (configType.toLowerCase()) {
    case 'channel':
      return ALL_CHANNELS_CONFIG_FILES.includes(file);
    case 'chain':
      return ALL_CHAINS_CONFIG_FILES.includes(file);
    case 'other':
      return ALL_OTHER_CONFIG_FILES.includes(file);
    default:
      throw new errors.InvalidConfigType();
  }
}

// Converts the parsed config file to dict
function parsedConfigToDict(config) {
  const sections = config.sections();
  return sections.reduce((map, obj) => {
    map[obj] = config.items(obj);
    return map;
  }, {});
}

module.exports = {
  getConfigPath,
  fileValid,

  // Reads the config given the full configPath
  readConfig: (configPath) => {
    const cp = new ConfigParser();
    cp.read(configPath);
    return parsedConfigToDict(cp);
  },

  // Writes the config to the location specified by configPath
  writeConfig: (configPath, data) => {
    const cp = new ConfigParser();

    // Generate config from dict
    Object.keys(data)
      .forEach((key) => {
        cp.addSection(key);
        Object.keys(data[key])
          .forEach((subkey) => {
            cp.set(key, subkey, data[key][subkey]);
          });
      });

    // Get config location where the write should take place, create folders if
    // they do not exist and after write the config to the location.
    const configLocation = getConfigLocation(configPath);
    fs.mkdir(configLocation, { recursive: true }, (err) => {
      if (err && err.code !== 'EEXIST') throw err;
      cp.write(configPath);
    });
  },
};

// TODO: Wait for writing to be succesfull, therefore ins erver make async await
//       and give more meaningful messages .. need to also do try catch
//     : Make sure that if './config' does not exist the function works (Start from here tomorrow)
//     : Check if folder exists before writing
