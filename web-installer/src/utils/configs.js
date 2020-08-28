const ConfigParser = require('configparser');
const path = require('path');

const USER_CONFIG_TELEGRAM = 'user_config_telegram.ini';
const USER_CONFIG_EMAIL = 'user_config_email.ini';
const USER_CONFIG_TWILIO = 'user_config_twilio.ini';
const USER_CONFIG_PAGERDUTY = 'user_config_pagerduty.ini';
const USER_CONFIG_OPSGENIE = 'user_config_opsgenie.ini';
const USER_CONFIG_NODES = 'user_config_nodes.ini';
const USER_CONFIG_REPOS = 'user_config_repos.ini';
const USER_CONFIG_UI = 'user_config_ui.ini';
const INTERNAL_CONFIG_MAIN = 'internal_config_main.ini';
const INTERNAL_CONFIG_ALERTS = 'internal_config_alerts.ini';
const ALL_CONFIG_FILES = [
  USER_CONFIG_MAIN, USER_CONFIG_NODES, USER_CONFIG_REPOS,
  INTERNAL_CONFIG_MAIN, INTERNAL_CONFIG_ALERTS,
];

const CHANNELS_CONFIGS_FOLDER = 'channels';

const

function getConfigPath(filePath, file) {
  return path.join('config', filePath, file);
}

function parsedConfigToDict(config) {
  const sections = config.sections();
  return sections.reduce((map, obj) => {
    map[obj] = config.items(obj);
    return map;
  }, {});
}

module.exports = {
  USER_CONFIG_MAIN,
  USER_CONFIG_NODES,
  USER_CONFIG_REPOS,
  USER_CONFIG_UI,
  INTERNAL_CONFIG_MAIN,
  INTERNAL_CONFIG_ALERTS,
  ALL_CONFIG_FILES,

  toConfigPath: getConfigPath,

  readConfig: (filePath, file) => {
    const cp = new ConfigParser();
    cp.read(getConfigPath(filePath, file));
    return parsedConfigToDict(cp);
  },

  writeConfig: (file, data) => {
    const cp = new ConfigParser();

    Object.keys(data)
      .forEach((key) => {
        cp.addSection(key);
        Object.keys(data[key])
          .forEach((subkey) => {
            cp.set(key, subkey, data[key][subkey]);
          });
      });

    cp.write(getConfigPath(file));
  },
};
