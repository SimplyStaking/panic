const ConfigParser = require('configparser');
const path = require('path');

const USER_CONFIG_MAIN = 'user_config_main.ini';
const USER_CONFIG_NODES = 'user_config_nodes.ini';
const USER_CONFIG_REPOS = 'user_config_repos.ini';
const USER_CONFIG_UI = 'user_config_ui.ini';
const INTERNAL_CONFIG_MAIN = 'internal_config_main.ini';
const INTERNAL_CONFIG_ALERTS = 'internal_config_alerts.ini';
const ALL_CONFIG_FILES = [
    USER_CONFIG_MAIN, USER_CONFIG_NODES, USER_CONFIG_REPOS,
    INTERNAL_CONFIG_MAIN, INTERNAL_CONFIG_ALERTS,
];

function getConfigPath(file) {
    return path.join('config/', file);
}

function parsedConfigToDict(config) {
    const sections = config.sections();
    return sections.reduce((map, obj) => {
        map[obj] = config.items(obj);
        return map;
    }, {});
}

module.exports = {
    toConfigPath: getConfigPath,

    USER_CONFIG_MAIN,
    USER_CONFIG_NODES,
    USER_CONFIG_REPOS,
    USER_CONFIG_UI,
    INTERNAL_CONFIG_MAIN,
    INTERNAL_CONFIG_ALERTS,
    ALL_CONFIG_FILES,

    readConfig: (file) => {
        const cp = new ConfigParser();
        cp.read(getConfigPath(file));
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
