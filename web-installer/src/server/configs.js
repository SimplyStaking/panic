const ConfigParser = require('configparser');
const fs = require('fs');
const path = require('path');
const errors = require('./errors');
const msgs = require('./msgs');

// Channel configs and config locations
const USER_CONFIG_TELEGRAM = 'telegram_config.ini';
const USER_CONFIG_EMAIL = 'email_config.ini';
const USER_CONFIG_TWILIO = 'twilio_config.ini';
const USER_CONFIG_PAGERDUTY = 'pagerduty_config.ini';
const USER_CONFIG_OPSGENIE = 'opsgenie_config.ini';
const USER_CONFIG_SLACK = 'slack_config.ini';
const ALL_CHANNELS_CONFIG_FILES = [
  USER_CONFIG_TELEGRAM, USER_CONFIG_EMAIL, USER_CONFIG_TWILIO,
  USER_CONFIG_PAGERDUTY, USER_CONFIG_OPSGENIE, USER_CONFIG_SLACK,
];
const CHANNELS_CONFIGS_LOCATION = path.join('../config', 'channels');

// Chain configs and config locations
const USER_CONFIG_NODES = 'nodes_config.ini';
const USER_CONFIG_EVM_NODES = 'evm_nodes_config.ini';
const USER_CONFIG_WEIWATCHERS = 'weiwatchers_config.ini';
const USER_CONFIG_REPOS = 'github_repos_config.ini';
const USER_CONFIG_DOCKER = 'dockerhub_repos_config.ini';
const USER_CONFIG_CHANNELS = 'channels_config.ini';
const USER_CONFIG_ALERTS = 'alerts_config.ini';
const USER_CONFIG_REPEAT_ALERTS = 'repeat_alerts_config.ini';
const USER_CONFIG_THRESHOLD_ALERTS = 'threshold_alerts_config.ini';
const USER_CONFIG_TIMEWINDOW_ALERTS = 'timewindow_alerts_config.ini';
const USER_CONFIG_SEVERTY_ALERTS = 'severity_alerts_config.ini';
const USER_CONFIG_SYSTEMS = 'systems_config.ini';
const USER_CONFIG_PERIODIC = 'periodic_config.ini';
const ALL_CHAINS_CONFIG_FILES = [
  USER_CONFIG_NODES, USER_CONFIG_REPOS, USER_CONFIG_CHANNELS,
  USER_CONFIG_ALERTS, USER_CONFIG_REPEAT_ALERTS, USER_CONFIG_THRESHOLD_ALERTS,
  USER_CONFIG_TIMEWINDOW_ALERTS, USER_CONFIG_SEVERTY_ALERTS, USER_CONFIG_DOCKER,
  USER_CONFIG_SYSTEMS, USER_CONFIG_EVM_NODES, USER_CONFIG_WEIWATCHERS,
];
const COSMOS_CHAINS_CONFIGS_LOCATION = path.join('../config', 'chains', 'cosmos');
const SUBSTRATE_CHAINS_CONFIGS_LOCATION = path.join('../config', 'chains', 'substrate');
const CHAINLINK_CHAINS_CONFIGS_LOCATION = path.join('../config', 'chains', 'chainlink');
const GENERAL_CONFIGS_LOCATION = path.join('../config', 'general');

// Other configs and config locations
const USER_CONFIG_SYSTEM = 'user_config_systems.ini';
const ALL_GENERAL_CONFIG_FILES = [USER_CONFIG_SYSTEM, USER_CONFIG_ALERTS,
  USER_CONFIG_REPEAT_ALERTS, USER_CONFIG_THRESHOLD_ALERTS,
  USER_CONFIG_TIMEWINDOW_ALERTS, USER_CONFIG_SEVERTY_ALERTS,
  USER_CONFIG_SYSTEMS, USER_CONFIG_PERIODIC, USER_CONFIG_REPOS,
  USER_CONFIG_CHANNELS, USER_CONFIG_DOCKER,
];

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
      if (baseChain.toLowerCase() === 'chainlink') {
        return path.join(CHAINLINK_CHAINS_CONFIGS_LOCATION, chainName, file);
      }
      throw new errors.InvalidBaseChain();
    case 'general':
      return path.join(GENERAL_CONFIGS_LOCATION, file);
    default:
      throw new errors.InvalidConfigType();
  }
}

// Get the config file location. This function expects the full config path
function getConfigLocation(configPath) {
  return path.parse(configPath).dir;
}

// Get the config file from a path. This function expects the full config path.
function getConfigFileFromLocation(configPath) {
  return path.basename(configPath);
}

// This function returns true if 'file' is expected in the inferred location
function fileValid(configType, file) {
  switch (configType.toLowerCase()) {
    case 'channel':
      return ALL_CHANNELS_CONFIG_FILES.includes(file);
    case 'chain':
      return ALL_CHAINS_CONFIG_FILES.includes(file);
    case 'general':
      return ALL_GENERAL_CONFIG_FILES.includes(file);
    default:
      throw new errors.InvalidConfigType();
  }
}

// Converts the parsed config file to dict
function parsedConfigToDict(config) {
  const sections = config.sections();
  return sections.reduce((map, obj) => {
    // eslint-disable-next-line no-param-reassign
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
    const configFile = getConfigFileFromLocation(configPath);
    // For the below to work the 'config' folder must never be deleted
    try {
      fs.mkdirSync(configLocation, { recursive: true });
    } catch (err) {
      throw new errors.CouldNotWriteConfig(err, configFile, configPath);
    }
    // Check that the path exists before writing, otherwise throw an error.
    if (fs.existsSync(configLocation)) {
      cp.write(configPath);
    } else {
      const msg = new msgs.DirectoryNotCreated(configLocation);
      throw new errors.CouldNotWriteConfig(
        msg.message, configFile, configPath,
      );
    }
  },
};

// TODO: Wait for writing to be successfull, therefore in server make async await
//       and give more meaningful messages .. need to also do try catch
