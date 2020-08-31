import { InvalidChainType, InvalidConfigType } from './errors';

const ConfigParser = require('configparser');
const path = require('path');

const USER_CONFIG_TELEGRAM = 'user_config_telegram.ini';
const USER_CONFIG_EMAIL = 'user_config_email.ini';
const USER_CONFIG_TWILIO = 'user_config_twilio.ini';
const USER_CONFIG_PAGERDUTY = 'user_config_pagerduty.ini';
const USER_CONFIG_OPSGENIE = 'user_config_opsgenie.ini';
const ALL_CHANNELS_CONFIG_FILES = [
  USER_CONFIG_TELEGRAM, USER_CONFIG_EMAIL, USER_CONFIG_TWILIO,
  USER_CONFIG_PAGERDUTY, USER_CONFIG_OPSGENIE,
];
const CHANNELS_CONFIGS_PATH = path.join('config', 'channels');

const USER_CONFIG_NODES = 'user_config_nodes.ini';
const USER_CONFIG_REPOS = 'user_config_repos.ini';
const USER_CONFIG_KMS = 'user_config_kms.ini';
const USER_CONFIG_CHANNELS = 'user_config_channels.ini';
const USER_CONFIG_ALERTS = 'user_config_alerts.ini';
const ALL_CHAINS_CONFIG_FILES = [
  USER_CONFIG_NODES, USER_CONFIG_REPOS, USER_CONFIG_KMS, USER_CONFIG_CHANNELS,
  USER_CONFIG_ALERTS,
];
const COSMOS_CHAINS_CONFIGS_PATH = path.join('config', 'chains', 'cosmos');
const SUBSTRATE_CHAINS_CONFIGS_PATH = path.join(
  'config', 'chains', 'substrate',
);

const USER_CONFIG_UI = 'user_config_ui.ini';
const ALL_UI_CONFIG_FILES = [USER_CONFIG_UI];
const UI_CONFIGS_PATH = path.join('configs', 'ui');

const USER_CONFIG_SYSTEM = 'user_config_system.ini';
const ALL_OTHER_CONFIG_FILES = [USER_CONFIG_SYSTEM, USER_CONFIG_ALERTS];
const OTHER_CONFIGS_PATH = path.join('configs', 'other');

function getConfigPath(configType, file, chainName = null, baseChain = null) {
  switch (configType.toLowerCase()) {
    case 'channel':
      return path.join(CHANNELS_CONFIGS_PATH, file);
    case 'chain':
      if (baseChain.toLowerCase() === 'cosmos') {
        return path.join(COSMOS_CHAINS_CONFIGS_PATH, chainName, file);
      }
      if (baseChain.toLowerCase() === 'substrate') {
        return path.join(SUBSTRATE_CHAINS_CONFIGS_PATH, chainName, file);
      }
      throw new InvalidChainType();
    case 'ui':
      return path.join(UI_CONFIGS_PATH, file);
    case 'other':
      return path.join(OTHER_CONFIGS_PATH, file);
    default:
      throw new InvalidConfigType();
  }
}

function isFileValid(configType, file, baseChain = null) {
  switch (configType.toLowerCase()) {
    case 'channel':
      return ALL_CHANNELS_CONFIG_FILES.includes(file);
    case 'chain':
      if (baseChain.toLowerCase() === 'cosmos') {
        return COSMOS_CHAINS_CONFIGS_PATH.includes(file);
      }
      if (baseChain.toLowerCase() === 'substrate') {
        return SUBSTRATE_CHAINS_CONFIGS_PATH.includes(file);
      }
      throw new InvalidChainType();
    case 'ui':
      return ALL_UI_CONFIG_FILES.includes(file);
    case 'other':
      return ALL_OTHER_CONFIG_FILES.includes(file);
    default:
      throw new InvalidConfigType();
  }
}

function parsedConfigToDict(config) {
  const sections = config.sections();
  return sections.reduce((map, obj) => {
    map[obj] = config.items(obj);
    return map;
  }, {});
}

module.exports = {
  ALL_CHANNELS_CONFIG_FILES,
  ALL_CHAINS_CONFIG_FILES,
  ALL_UI_CONFIG_FILES,
  ALL_OTHER_CONFIG_FILES,

  getConfigPath,
  isFileValid,

  readConfig: (configPath) => {
    const cp = new ConfigParser();
    cp.read(configPath);
    return parsedConfigToDict(cp);
  },

  writeConfig: (configPath, data) => {
    const cp = new ConfigParser();

    Object.keys(data)
      .forEach((key) => {
        cp.addSection(key);
        Object.keys(data[key])
          .forEach((subkey) => {
            cp.set(key, subkey, data[key][subkey]);
          });
      });

    cp.write(configPath);
  },
};
