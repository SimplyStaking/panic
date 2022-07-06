/**
 * Helper function to reduce code duplication when removing a chain
 * and all it's data.
 * @param currentConfig is the current configuration of the chain
 * @param stateData is the data of the Channel which is in redux state
 * @param chainID is the identifier of the current chain which is being deleted
 * @param removeDetails is the function which is used to remove the channel data from the chain
 */
export function clearChannelData(currentConfig, stateData, chainID, removeDetails) {
  let payload = {};
  let index = 0;
  for (let i = 0; i < stateData.allIds.length; i += 1) {
    payload = JSON.parse(JSON.stringify(stateData.byId[stateData.allIds[i]]));
    if (payload.parent_ids.includes(chainID)) {
      index = payload.parent_ids.indexOf(chainID);
      if (index > -1) {
        payload.parent_ids.splice(index, 1);
      }
      index = payload.parent_names.indexOf(currentConfig.chain_name);
      if (index > -1) {
        payload.parent_names.splice(index, 1);
      }
      removeDetails(payload);
    }
  }
}

/**
 * Helper function to reduce code duplication when removing a chain
 * and all it's data.
 * @param currentConfig is the current configuration of the chain
 * @param type this is the type of data we are going to be removing
 * @param removeDetails is the function which is used to remove the data source from the chain
 */
export function clearDataSources(currentConfig, type, removeDataSourceDetails, payload) {
  for (let i = 0; i < currentConfig[type].length; i += 1) {
    // eslint-disable-next-line no-param-reassign
    payload.id = currentConfig[type][i];
    removeDataSourceDetails(payload);
  }
}

/**
 * @param value is the variable to check the node name against
 * @param configs is a list of configuration files which need to be iterated
 */
export function checkSourceName(value, ...configs) {
  for (let i = 0; i < configs.length; i += 1) {
    const config = configs[i];

    for (let j = 0; j < config.allIds.length; j += 1) {
      if (config.byId[config.allIds[j]].name === value) {
        return false;
      }
    }
  }

  return true;
}

/**
 * @param value is the variable to check the repo name against
 * @param config dockerhub configuration file which needs to be iterated
 */
export function checkDockerHubRepoExists(value, config) {
  if (value === undefined) {
    return true;
  }
  let valueToTest = value;
  for (let j = 0; j < config.allIds.length; j += 1) {
    let fullRepoName = `library/${config.byId[config.allIds[j]].repo_name}`;
    if (valueToTest.includes('/')) {
      fullRepoName = `${config.byId[config.allIds[j]].repo_namespace}/${config.byId[config.allIds[j]].repo_name}`;
    } else {
      valueToTest = `library/${value}`;
    }
    if (fullRepoName === valueToTest) {
      return false;
    }
  }
  return true;
}

/**
 * @param value is the variable to check the repo name against
 * @param config github configuration file which needs to be iterated
 */
export function checkGitHubRepoExists(value, config) {
  if (value === undefined) {
    return true;
  }
  for (let j = 0; j < config.allIds.length; j += 1) {
    if (value === config.byId[config.allIds[j]].repo_name) {
      return false;
    }
  }
  return true;
}

/**
 * @param value is the variable to check the chain name against
 * @param configs is a list of configuration files which need to be iterated
 */
export function checkChainName(value, ...configs) {
  for (let i = 0; i < configs.length; i += 1) {
    const config = configs[i];

    for (let j = 0; j < config.allIds.length; j += 1) {
      if (config.byId[config.allIds[j]].chain_name === value) {
        return false;
      }
    }
  }

  return true;
}

/**
 * @param value is the variable to check the channel name against
 * @param configs is a list of configuration files which need to be iterated
 */
export function checkChannelName(value, ...configs) {
  for (let i = 0; i < configs.length; i += 1) {
    const config = configs[i];

    for (let j = 0; j < config.allIds.length; j += 1) {
      if (config.byId[config.allIds[j]].channel_name === value) {
        return false;
      }
    }
  }

  return true;
}

/**
 * @param value is the variable to check for a square bracket
 */
export function checkIfDoesNotContainsSquareBracket(value) {
  if (!value) {
    return true;
  }
  return !(value.includes('[') || value.includes(']'));
}

export function setAlertsData(chainConfig, currentChainId) {
  const repeatAlertsConfig = {};
  const thresholdAlertsConfig = {};
  const timeWindowAlertsConfig = {};
  const severityAlertsConfig = {};

  for (let i = 0; i < chainConfig.repeatAlerts.allIds.length; i += 1) {
    const id = chainConfig.repeatAlerts.allIds[i];
    repeatAlertsConfig[id] = {};
    repeatAlertsConfig[id].name = chainConfig.repeatAlerts.byId[id].identifier;
    repeatAlertsConfig[id].parent_id = currentChainId;
    repeatAlertsConfig[id].enabled = chainConfig.repeatAlerts.byId[id].enabled;
    repeatAlertsConfig[id].critical_enabled = chainConfig.repeatAlerts.byId[id].critical.enabled;
    repeatAlertsConfig[id].critical_repeat = chainConfig.repeatAlerts.byId[id].critical.repeat;
    repeatAlertsConfig[id].critical_repeat_enabled = chainConfig.repeatAlerts.byId[id]
      .critical.repeat_enabled;
    repeatAlertsConfig[id].warning_enabled = chainConfig.repeatAlerts.byId[id].warning.enabled;
    repeatAlertsConfig[id].warning_repeat = chainConfig.repeatAlerts.byId[id].warning.repeat;
  }

  for (let i = 0; i < chainConfig.thresholdAlerts.allIds.length; i += 1) {
    const id = chainConfig.thresholdAlerts.allIds[i];
    thresholdAlertsConfig[id] = {};
    thresholdAlertsConfig[id].name = chainConfig.thresholdAlerts.byId[id].identifier;
    thresholdAlertsConfig[id].parent_id = currentChainId;
    thresholdAlertsConfig[id].enabled = chainConfig.thresholdAlerts.byId[id].enabled;
    thresholdAlertsConfig[id].warning_threshold = chainConfig.thresholdAlerts.byId[id]
      .warning.threshold;
    thresholdAlertsConfig[id].warning_enabled = chainConfig.thresholdAlerts.byId[id]
      .warning.enabled;
    thresholdAlertsConfig[id].critical_threshold = chainConfig.thresholdAlerts.byId[id]
      .critical.threshold;
    thresholdAlertsConfig[id].critical_repeat = chainConfig.thresholdAlerts.byId[id]
      .critical.repeat;
    thresholdAlertsConfig[id].critical_repeat_enabled = chainConfig.thresholdAlerts.byId[id]
      .critical.repeat_enabled;
    thresholdAlertsConfig[id].critical_enabled = chainConfig.thresholdAlerts.byId[id]
      .critical.enabled;
  }

  for (let i = 0; i < chainConfig.timeWindowAlerts.allIds.length; i += 1) {
    const id = chainConfig.timeWindowAlerts.allIds[i];
    timeWindowAlertsConfig[id] = {};
    timeWindowAlertsConfig[id].name = chainConfig.timeWindowAlerts.byId[id].identifier;
    timeWindowAlertsConfig[id].parent_id = currentChainId;
    timeWindowAlertsConfig[id].enabled = chainConfig.timeWindowAlerts.byId[id].enabled;
    timeWindowAlertsConfig[id].warning_threshold = chainConfig.timeWindowAlerts.byId[id]
      .warning.threshold;
    timeWindowAlertsConfig[id].warning_time_window = chainConfig.timeWindowAlerts.byId[id]
      .warning.time_window;
    timeWindowAlertsConfig[id].warning_enabled = chainConfig.timeWindowAlerts.byId[id]
      .warning.enabled;
    timeWindowAlertsConfig[id].critical_threshold = chainConfig.timeWindowAlerts.byId[id]
      .critical.threshold;
    timeWindowAlertsConfig[id].critical_time_window = chainConfig.timeWindowAlerts.byId[id]
      .critical.time_window;
    timeWindowAlertsConfig[id].critical_repeat = chainConfig.timeWindowAlerts.byId[id]
      .critical.repeat;
    timeWindowAlertsConfig[id].critical_repeat_enabled = chainConfig.timeWindowAlerts.byId[id]
      .critical.repeat_enabled;
    timeWindowAlertsConfig[id].critical_enabled = chainConfig.timeWindowAlerts.byId[id]
      .critical.enabled;
  }

  for (let i = 0; i < chainConfig.severityAlerts.allIds.length; i += 1) {
    const id = chainConfig.severityAlerts.allIds[i];
    severityAlertsConfig[id] = {};
    severityAlertsConfig[id].name = chainConfig.severityAlerts.byId[id].identifier;
    severityAlertsConfig[id].parent_id = currentChainId;
    severityAlertsConfig[id].enabled = chainConfig.severityAlerts.byId[id].enabled;
    severityAlertsConfig[id].severity = chainConfig.severityAlerts.byId[id].severity;
  }

  return {
    ...repeatAlertsConfig,
    ...thresholdAlertsConfig,
    ...timeWindowAlertsConfig,
    ...severityAlertsConfig,
  };
}
