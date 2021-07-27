/* eslint-disable camelcase */
/* eslint-disable no-await-in-loop */
import React, { Component } from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { ToastsStore } from 'react-toasts';
import { LoadConfigButton } from 'utils/buttons';
import { getConfigPaths, getConfig } from 'utils/data';
import { GENERAL } from 'constants/constants';
import {
  addTelegram,
  addTwilio,
  addEmail,
  addPagerDuty,
  addOpsGenie,
  addSlack,
} from 'redux/actions/channelActions';
import {
  addDockerHub,
  addSystem,
  addRepository,
  loadThresholdAlertsGeneral,
} from 'redux/actions/generalActions';
import {
  addChainCosmos,
  addNodeCosmos,
  loadRepeatAlertsCosmos,
  loadTimeWindowAlertsCosmos,
  loadThresholdAlertsCosmos,
  loadSeverityAlertsCosmos,
  resetCurrentChainIdCosmos,
} from 'redux/actions/cosmosActions';
import {
  addNodeSubstrate,
  addChainSubstrate,
  loadRepeatAlertsSubstrate,
  loadTimeWindowAlertsSubstrate,
  loadThresholdAlertsSubstrate,
  loadSeverityAlertsSubstrate,
  resetCurrentChainIdSubstrate,
} from 'redux/actions/substrateActions';
import {
  addNodeChainlink,
  addChainChainlink,
  loadRepeatAlertsChainlink,
  loadTimeWindowAlertsChainlink,
  loadThresholdAlertsChainlink,
  loadSeverityAlertsChainlink,
  resetCurrentChainIdChainlink,
} from 'redux/actions/chainlinkActions';
import {
  generalThresholdAlerts,
} from 'redux/reducers/generalReducer';
import {
  cosmosRepeatAlerts,
  cosmosThresholdAlerts,
  cosmosTimeWindowAlerts,
  cosmosSeverityAlerts,
} from 'redux/reducers/cosmosChainsReducer';
import {
  chainlinkRepeatAlerts,
  chainlinkThresholdAlerts,
  chainlinkTimeWindowAlerts,
  chainlinkSeverityAlerts,
} from 'redux/reducers/chainlinkChainsReducer';
import {
  substrateRepeatAlerts,
  substrateThresholdAlerts,
  substrateTimeWindowAlerts,
  substrateSeverityAlerts,
} from 'redux/reducers/substrateChainsReducer';

// List of all the data that needs to be saved in the server
const mapStateToProps = (state) => ({
  // Cosmos related data
  cosmosChains: state.CosmosChainsReducer,
  cosmosNodes: state.CosmosNodesReducer,

  // substrate related data
  substrateChains: state.SubstrateChainsReducer,
  substrateNodes: state.SubstrateNodesReducer,

  // Chainlink related data
  chainlinkChains: state.ChainlinkChainsReducer,
  chainlinkNodes: state.ChainlinkNodesReducer,

  // Channels related data
  emails: state.EmailsReducer,
  opsgenies: state.OpsGenieReducer,
  pagerduties: state.PagerDutyReducer,
  telegrams: state.TelegramsReducer,
  twilios: state.TwiliosReducer,
  slacks: state.SlacksReducer,

  // General data related to
  githubRepositories: state.GitHubRepositoryReducer,
  general: state.GeneralReducer.byId[GENERAL],
  systems: state.SystemsReducer,
  periodic: state.PeriodicReducer,
});

function mapDispatchToProps(dispatch) {
  return {
    addEmailDetails: (details) => dispatch(addEmail(details)),
    addTelegramDetails: (details) => dispatch(addTelegram(details)),
    addSlackDetails: (details) => dispatch(addSlack(details)),
    addTwilioDetails: (details) => dispatch(addTwilio(details)),
    addPagerDutyDetails: (details) => dispatch(addPagerDuty(details)),
    addOpsGenieDetails: (details) => dispatch(addOpsGenie(details)),
    addChainCosmosDetails: (details) => dispatch(addChainCosmos(details)),
    addNodeCosmosDetails: (details) => dispatch(addNodeCosmos(details)),
    clearChainIdCosmos: () => dispatch(resetCurrentChainIdCosmos()),
    addChainSubstrateDetails: (details) => dispatch(addChainSubstrate(details)),
    addNodeSubstrateDetails: (details) => dispatch(addNodeSubstrate(details)),
    clearChainIdSubstrate: () => dispatch(resetCurrentChainIdSubstrate()),
    addChainChainlinkDetails: (details) => dispatch(addChainChainlink(details)),
    addNodeChainlinkDetails: (details) => dispatch(addNodeChainlink(details)),
    clearChainIdChainlink: () => dispatch(resetCurrentChainIdChainlink()),
    addSystemDetails: (details) => dispatch(addSystem(details)),
    addDockerHubDetails: (details) => dispatch(addDockerHub(details)),
    addRepositoryDetails: (details) => dispatch(addRepository(details)),
    loadThresholdAlertsGeneralDetails: (details) => dispatch(loadThresholdAlertsGeneral(details)),
    loadRepeatAlertsCosmosDetails: (details) => dispatch(loadRepeatAlertsCosmos(details)),
    loadTimeWindowAlertsCosmosDetails: (details) => dispatch(loadTimeWindowAlertsCosmos(details)),
    loadThresholdAlertsCosmosDetails: (details) => dispatch(loadThresholdAlertsCosmos(details)),
    loadSeverityAlertsCosmosDetails: (details) => dispatch(loadSeverityAlertsCosmos(details)),
    loadRepeatAlertsSubstrateDetails: (details) => dispatch(loadRepeatAlertsSubstrate(details)),
    loadTimeWindowAlertsSubstrateDetails: (details) => dispatch(
      loadTimeWindowAlertsSubstrate(details),
    ),
    loadThresholdAlertsSubstrateDetails: (details) => dispatch(
      loadThresholdAlertsSubstrate(details),
    ),
    loadSeverityAlertsSubstrateDetails: (details) => dispatch(loadSeverityAlertsSubstrate(details)),
    loadRepeatAlertsChainlinkDetails: (details) => dispatch(loadRepeatAlertsChainlink(details)),
    loadTimeWindowAlertsChainlinkDetails: (details) => dispatch(
      loadTimeWindowAlertsChainlink(details),
    ),
    loadThresholdAlertsChainlinkDetails: (details) => dispatch(
      loadThresholdAlertsChainlink(details),
    ),
    loadSeverityAlertsChainlinkDetails: (details) => dispatch(loadSeverityAlertsChainlink(details)),
  };
}

// Checking if the current chain has been setup and if not set it up
function CreateChain(config, chainName, addChain) {
  const singleConfig = config[Object.keys(config)[0]];
  addChain({ id: singleConfig.parent_id, chain_name: chainName });
}

class LoadConfig extends Component {
  constructor(props) {
    super(props);
    this.loadConfigs = this.loadConfigs.bind(this);
    this.onClick = this.onClick.bind(this);
  }

  onClick() {
    const { handleClose } = this.props;
    this.loadConfigs();
    handleClose();
  }

  async loadConfigs() {
    const {
      addEmailDetails,
      addTelegramDetails,
      addTwilioDetails,
      addPagerDutyDetails,
      addOpsGenieDetails,
      addSlackDetails,
      addDockerHubDetails,
      addSystemDetails,
      addRepositoryDetails,
      addChainCosmosDetails,
      addChainSubstrateDetails,
      addChainChainlinkDetails,
      addNodeCosmosDetails,
      addNodeSubstrateDetails,
      addNodeChainlinkDetails,
      loadThresholdAlertsGeneralDetails,
      loadRepeatAlertsCosmosDetails,
      loadTimeWindowAlertsCosmosDetails,
      loadThresholdAlertsCosmosDetails,
      loadSeverityAlertsCosmosDetails,
      loadRepeatAlertsSubstrateDetails,
      loadTimeWindowAlertsSubstrateDetails,
      loadThresholdAlertsSubstrateDetails,
      loadSeverityAlertsSubstrateDetails,
      loadRepeatAlertsChainlinkDetails,
      loadTimeWindowAlertsChainlinkDetails,
      loadThresholdAlertsChainlinkDetails,
      loadSeverityAlertsChainlinkDetails,
      clearChainIdChainlink,
      clearChainIdSubstrate,
      clearChainIdCosmos,
    } = this.props;

    ToastsStore.info('Attempting to Load Configuration.', 5000);
    const paths = await getConfigPaths();
    const files = paths.data.result;
    let filePath;
    let config;
    try {
      for (let i = 0; i < files.length; i += 1) {
        filePath = files[i].split('/');
        if (filePath[1] === 'general') {
          if (filePath[2] === 'github_repos_config.ini') {
            config = await getConfig('general', 'github_repos_config.ini', '', '');
            Object.values(config.data.result).forEach((value) => {
              const payload = JSON.parse(JSON.stringify(value));
              payload.monitor_repo = payload.monitor_repo === 'true';
              addRepositoryDetails(payload);
            });
          } else if (filePath[2] === 'systems_config.ini') {
            config = await getConfig('general', 'systems_config.ini', '', '');
            Object.values(config.data.result).forEach((value) => {
              const payload = JSON.parse(JSON.stringify(value));
              payload.monitor_system = payload.monitor_system === 'true';
              addSystemDetails(payload);
            });
          } else if (filePath[2] === 'dockerhub_repos_config.ini') {
            config = await getConfig('general', 'dockerhub_repos_config.ini', '', '');
            Object.values(config.data.result).forEach((value) => {
              const payload = JSON.parse(JSON.stringify(value));
              payload.monitor_docker = payload.monitor_docker === 'true';
              addDockerHubDetails(payload);
            });
          } else if (filePath[2] === 'alerts_config.ini') {
            config = await getConfig('general', 'alerts_config.ini', '', '');
            // Create copies of alerts, if there are missing alerts in the
            // configuration file we'll just use the pre-done alerts.
            const thresholdAlerts = JSON.parse(
              JSON.stringify(generalThresholdAlerts),
            );
            let parent_id;
            Object.entries(config.data.result).forEach((entry) => {
              const [key, value] = entry;
              parent_id = value.parent_id;

              if (key in thresholdAlerts.byId) {
                thresholdAlerts.byId[key].parent_id = value.parent_id;
                const warning = {
                  threshold: value.warning_threshold,
                  enabled: value.warning_enabled === 'true',
                };
                const critical = {
                  threshold: value.critical_threshold,
                  repeat: value.critical_repeat,
                  repeat_enabled: value.critical_repeat_enabled === 'true',
                  enabled: value.critical_enabled === 'true',
                };
                thresholdAlerts.byId[key].warning = warning;
                thresholdAlerts.byId[key].critical = critical;
                thresholdAlerts.byId[key].enabled = value.enabled === 'true';
              }
            });
            loadThresholdAlertsGeneralDetails({ parent_id, alerts: thresholdAlerts });
          }
        } else if (filePath[1] === 'chains') {
          if (filePath[2] === 'cosmos') {
            if (filePath[4] === 'github_repos_config.ini') {
              config = await getConfig('chain', 'github_repos_config.ini', filePath[3], 'cosmos');
              CreateChain(config.data.result, filePath[3], addChainCosmosDetails);
              Object.values(config.data.result).forEach((value) => {
                const payload = JSON.parse(JSON.stringify(value));
                payload.monitor_repo = payload.monitor_repo === 'true';
                addRepositoryDetails(payload);
              });
            } else if (filePath[4] === 'dockerhub_repos_config.ini') {
              config = await getConfig('chain', 'dockerhub_repos_config.ini', filePath[3], 'cosmos');
              CreateChain(config.data.result, filePath[3], addChainCosmosDetails);
              Object.values(config.data.result).forEach((value) => {
                const payload = JSON.parse(JSON.stringify(value));
                payload.monitor_docker = payload.monitor_docker === 'true';
                addDockerHubDetails(payload);
              });
            } else if (filePath[4] === 'nodes_config.ini') {
              config = await getConfig('chain', 'nodes_config.ini', filePath[3], 'cosmos');
              CreateChain(config.data.result, filePath[3], addChainCosmosDetails);
              Object.values(config.data.result).forEach((value) => {
                const node = JSON.parse(JSON.stringify(value));
                node.monitor_tendermint = node.monitor_tendermint === 'true';
                node.monitor_rpc = node.monitor_rpc === 'true';
                node.monitor_prometheus = node.monitor_prometheus === 'true';
                node.monitor_system = node.monitor_system === 'true';
                node.is_archive_node = node.is_archive_node === 'true';
                node.is_validator = node.is_validator === 'true';
                node.monitor_node = node.monitor_node === 'true';
                node.use_as_data_source = node.use_as_data_source === 'true';
                addNodeCosmosDetails(node);
              });
            } else if (filePath[4] === 'alerts_config.ini') {
              config = await getConfig(
                'chain',
                'alerts_config.ini',
                filePath[3],
                'cosmos',
              );
              CreateChain(config.data.result, filePath[3], addChainCosmosDetails);
              // Create copies of alerts, if there are missing alerts in the
              // configuration file we'll just use the pre-done alerts.
              const repeatAlerts = JSON.parse(JSON.stringify(cosmosRepeatAlerts));
              const thresholdAlerts = JSON.parse(JSON.stringify(cosmosThresholdAlerts));
              const timeWindowAlerts = JSON.parse(JSON.stringify(cosmosTimeWindowAlerts));
              const severityAlerts = JSON.parse(JSON.stringify(cosmosSeverityAlerts));
              let parent_id;
              Object.entries(config.data.result).forEach((entry) => {
                const [key, value] = entry;
                parent_id = value.parent_id;
                if (key in repeatAlerts.byId) {
                  repeatAlerts.byId[key].parent_id = value.parent_id;
                  const warning = {
                    repeat: value.warning_repeat,
                    enabled: value.warning_enabled === 'true',
                  };
                  const critical = {
                    repeat: value.critical_repeat,
                    repeat_enabled: value.critical_repeat_enabled === 'true',
                    enabled: value.critical_enabled === 'true',
                  };
                  repeatAlerts.byId[key].warning = warning;
                  repeatAlerts.byId[key].critical = critical;
                  repeatAlerts.byId[key].enabled = value.enabled === 'true';
                } else if (key in thresholdAlerts.byId) {
                  thresholdAlerts.byId[key].parent_id = value.parent_id;
                  const warning = {
                    threshold: value.warning_threshold,
                    enabled: value.warning_enabled === 'true',
                  };
                  const critical = {
                    threshold: value.critical_threshold,
                    repeat: value.critical_repeat,
                    repeat_enabled: value.critical_repeat_enabled === 'true',
                    enabled: value.critical_enabled === 'true',
                  };
                  thresholdAlerts.byId[key].warning = warning;
                  thresholdAlerts.byId[key].critical = critical;
                  thresholdAlerts.byId[key].enabled = value.enabled === 'true';
                } else if (key in timeWindowAlerts.byId) {
                  timeWindowAlerts.byId[key].parent_id = value.parent_id;
                  const warning = {
                    threshold: value.warning_threshold,
                    time_window: value.warning_time_window,
                    enabled: value.warning_enabled === 'true',
                  };
                  const critical = {
                    threshold: value.critical_threshold,
                    time_window: value.critical_time_window,
                    repeat: value.critical_repeat,
                    repeat_enabled: value.critical_repeat_enabled === 'true',
                    enabled: value.critical_enabled === 'true',
                  };
                  timeWindowAlerts.byId[key].warning = warning;
                  timeWindowAlerts.byId[key].critical = critical;
                  timeWindowAlerts.byId[key].enabled = value.enabled === 'true';
                } else if (key in severityAlerts.byId) {
                  severityAlerts.byId[key].parent_id = value.parent_id;
                  severityAlerts.byId[key].severity = value.severity;
                  severityAlerts.byId[key].enabled = value.enabled === 'true';
                }
              });
              loadRepeatAlertsCosmosDetails(
                {
                  chain_name: filePath[3],
                  parent_id,
                  alerts: repeatAlerts,
                },
              );
              loadTimeWindowAlertsCosmosDetails(
                {
                  chain_name: filePath[3],
                  parent_id,
                  alerts: timeWindowAlerts,
                },
              );
              loadThresholdAlertsCosmosDetails(
                {
                  chain_name: filePath[3],
                  parent_id,
                  alerts: thresholdAlerts,
                },
              );
              loadSeverityAlertsCosmosDetails(
                {
                  chain_name: filePath[3],
                  parent_id,
                  alerts: severityAlerts,
                },
              );
            }
          } else if (filePath[2] === 'substrate') {
            if (filePath[4] === 'github_repos_config.ini') {
              config = await getConfig('chain', 'github_repos_config.ini', filePath[3], 'substrate');
              CreateChain(config.data.result, filePath[3], addChainSubstrateDetails);
              Object.values(config.data.result).forEach((value) => {
                const payload = JSON.parse(JSON.stringify(value));
                payload.monitor_repo = payload.monitor_repo === 'true';
                addRepositoryDetails(payload);
              });
            } else if (filePath[4] === 'dockerhub_repos_config.ini') {
              config = await getConfig('chain', 'dockerhub_repos_config.ini', filePath[3], 'substrate');
              CreateChain(config.data.result, filePath[3], addChainSubstrateDetails);
              Object.values(config.data.result).forEach((value) => {
                const payload = JSON.parse(JSON.stringify(value));
                payload.monitor_docker = payload.monitor_docker === 'true';
                addDockerHubDetails(payload);
              });
            } else if (filePath[4] === 'nodes_config.ini') {
              config = await getConfig('chain', 'nodes_config.ini', filePath[3], 'substrate');
              CreateChain(config.data.result, filePath[3], addChainSubstrateDetails);
              Object.values(config.data.result).forEach((value) => {
                const node = JSON.parse(JSON.stringify(value));
                node.is_archive_node = node.is_archive_node === 'true';
                node.is_validator = node.is_validator === 'true';
                node.monitor_node = node.monitor_node === 'true';
                node.use_as_data_source = node.use_as_data_source === 'true';
                addNodeSubstrateDetails(node);
              });
            } else if (filePath[4] === 'alerts_config.ini') {
              config = await getConfig(
                'chain',
                'alerts_config.ini',
                filePath[3],
                'substrate',
              );
              CreateChain(config.data.result, filePath[3], addChainSubstrateDetails);
              // Create copies of alerts, if there are missing alerts in the
              // configuration file we'll just use the pre-done alerts.
              const repeatAlerts = JSON.parse(JSON.stringify(substrateRepeatAlerts));
              const thresholdAlerts = JSON.parse(JSON.stringify(substrateThresholdAlerts));
              const timeWindowAlerts = JSON.parse(JSON.stringify(substrateTimeWindowAlerts));
              const severityAlerts = JSON.parse(JSON.stringify(substrateSeverityAlerts));
              let parent_id;
              Object.entries(config.data.result).forEach((entry) => {
                const [key, value] = entry;
                parent_id = value.parent_id;
                if (key in repeatAlerts.byId) {
                  repeatAlerts.byId[key].parent_id = value.parent_id;
                  const warning = {
                    repeat: value.warning_repeat,
                    enabled: value.warning_enabled === 'true',
                  };
                  const critical = {
                    repeat: value.critical_repeat,
                    repeat_enabled: value.critical_repeat_enabled === 'true',
                    enabled: value.critical_enabled === 'true',
                  };
                  repeatAlerts.byId[key].warning = warning;
                  repeatAlerts.byId[key].critical = critical;
                  repeatAlerts.byId[key].enabled = value.enabled === 'true';
                } else if (key in thresholdAlerts.byId) {
                  thresholdAlerts.byId[key].parent_id = value.parent_id;
                  const warning = {
                    threshold: value.warning_threshold,
                    enabled: value.warning_enabled === 'true',
                  };
                  const critical = {
                    threshold: value.critical_threshold,
                    repeat: value.critical_repeat,
                    repeat_enabled: value.critical_repeat_enabled === 'true',
                    enabled: value.critical_enabled === 'true',
                  };
                  thresholdAlerts.byId[key].warning = warning;
                  thresholdAlerts.byId[key].critical = critical;
                  thresholdAlerts.byId[key].enabled = value.enabled === 'true';
                } else if (key in timeWindowAlerts.byId) {
                  timeWindowAlerts.byId[key].parent_id = value.parent_id;
                  const warning = {
                    threshold: value.warning_threshold,
                    time_window: value.warning_time_window,
                    enabled: value.warning_enabled === 'true',
                  };
                  const critical = {
                    threshold: value.critical_threshold,
                    time_window: value.critical_time_window,
                    repeat: value.critical_repeat,
                    repeat_enabled: value.critical_repeat_enabled === 'true',
                    enabled: value.critical_enabled === 'true',
                  };
                  timeWindowAlerts.byId[key].warning = warning;
                  timeWindowAlerts.byId[key].critical = critical;
                  timeWindowAlerts.byId[key].enabled = value.enabled === 'true';
                } else if (key in severityAlerts.byId) {
                  severityAlerts.byId[key].parent_id = value.parent_id;
                  severityAlerts.byId[key].severity = value.severity;
                  severityAlerts.byId[key].enabled = value.enabled === 'true';
                }
              });
              loadRepeatAlertsSubstrateDetails(
                {
                  chain_name: filePath[3],
                  parent_id,
                  alerts: repeatAlerts,
                },
              );
              loadTimeWindowAlertsSubstrateDetails(
                {
                  chain_name: filePath[3],
                  parent_id,
                  alerts: timeWindowAlerts,
                },
              );
              loadThresholdAlertsSubstrateDetails(
                {
                  chain_name: filePath[3],
                  parent_id,
                  alerts: thresholdAlerts,
                },
              );
              loadSeverityAlertsSubstrateDetails(
                {
                  chain_name: filePath[3],
                  parent_id,
                  alerts: severityAlerts,
                },
              );
            }
          } else if (filePath[2] === 'chainlink') {
            if (filePath[4] === 'github_repos_config.ini') {
              config = await getConfig('chain', 'github_repos_config.ini', filePath[3], 'chainlink');
              CreateChain(config.data.result, filePath[3], addChainChainlinkDetails);
              Object.values(config.data.result).forEach((value) => {
                const payload = JSON.parse(JSON.stringify(value));
                payload.monitor_repo = payload.monitor_repo === 'true';
                addRepositoryDetails(payload);
              });
            } else if (filePath[4] === 'dockerhub_repos_config.ini') {
              config = await getConfig('chain', 'dockerhub_repos_config.ini', filePath[3], 'chainlink');
              CreateChain(config.data.result, filePath[3], addChainChainlinkDetails);
              Object.values(config.data.result).forEach((value) => {
                const payload = JSON.parse(JSON.stringify(value));
                payload.monitor_docker = payload.monitor_docker === 'true';
                addDockerHubDetails(payload);
              });
            } else if (filePath[4] === 'nodes_config.ini') {
              config = await getConfig('chain', 'nodes_config.ini', filePath[3], 'chainlink');
              CreateChain(config.data.result, filePath[3], addChainChainlinkDetails);
              Object.values(config.data.result).forEach((value) => {
                const node = JSON.parse(JSON.stringify(value));
                if (node.node_prometheus_urls.length === 0) {
                  node.node_prometheus_urls = [];
                } else {
                  node.node_prometheus_urls = node.node_prometheus_urls.split(',');
                }
                node.monitor_prometheus = node.monitor_prometheus === 'true';
                node.monitor_node = node.monitor_node === 'true';
                addNodeChainlinkDetails(node);
              });
            } else if (filePath[4] === 'systems_config.ini') {
              config = await getConfig('chain', 'systems_config.ini', filePath[3], 'chainlink');
              CreateChain(config.data.result, filePath[3], addChainChainlinkDetails);
              Object.values(config.data.result).forEach((value) => {
                const payload = JSON.parse(JSON.stringify(value));
                payload.monitor_system = payload.monitor_system === 'true';
                addSystemDetails(payload);
              });
            } else if (filePath[4] === 'alerts_config.ini') {
              config = await getConfig(
                'chain',
                'alerts_config.ini',
                filePath[3],
                'chainlink',
              );
              CreateChain(config.data.result, filePath[3], addChainChainlinkDetails);
              // Create copies of alerts, if there are missing alerts in the
              // configuration file we'll just use the pre-done alerts.
              const repeatAlerts = JSON.parse(JSON.stringify(chainlinkRepeatAlerts));
              const thresholdAlerts = JSON.parse(JSON.stringify(chainlinkThresholdAlerts));
              const timeWindowAlerts = JSON.parse(JSON.stringify(chainlinkTimeWindowAlerts));
              const severityAlerts = JSON.parse(JSON.stringify(chainlinkSeverityAlerts));
              let parent_id;
              Object.entries(config.data.result).forEach((entry) => {
                const [key, value] = entry;
                parent_id = value.parent_id;
                if (key in repeatAlerts.byId) {
                  repeatAlerts.byId[key].parent_id = value.parent_id;
                  const warning = {
                    repeat: value.warning_repeat,
                    enabled: value.warning_enabled === 'true',
                  };
                  const critical = {
                    repeat: value.critical_repeat,
                    enabled: value.critical_enabled === 'true',
                  };
                  repeatAlerts.byId[key].warning = warning;
                  repeatAlerts.byId[key].critical = critical;
                  repeatAlerts.byId[key].enabled = value.enabled === 'true';
                } else if (key in thresholdAlerts.byId) {
                  thresholdAlerts.byId[key].parent_id = value.parent_id;
                  const warning = {
                    threshold: value.warning_threshold,
                    enabled: value.warning_enabled === 'true',
                  };
                  const critical = {
                    threshold: value.critical_threshold,
                    repeat: value.critical_repeat,
                    repeat_enabled: value.critical_repeat_enabled === 'true',
                    enabled: value.critical_enabled === 'true',
                  };
                  thresholdAlerts.byId[key].warning = warning;
                  thresholdAlerts.byId[key].critical = critical;
                  thresholdAlerts.byId[key].enabled = value.enabled === 'true';
                } else if (key in timeWindowAlerts.byId) {
                  timeWindowAlerts.byId[key].parent_id = value.parent_id;
                  const warning = {
                    threshold: value.warning_threshold,
                    time_window: value.warning_time_window,
                    enabled: value.warning_enabled === 'true',
                  };
                  const critical = {
                    threshold: value.critical_threshold,
                    time_window: value.critical_time_window,
                    repeat: value.critical_repeat,
                    repeat_enabled: value.critical_repeat_enabled === 'true',
                    enabled: value.critical_enabled === 'true',
                  };
                  timeWindowAlerts.byId[key].warning = warning;
                  timeWindowAlerts.byId[key].critical = critical;
                  timeWindowAlerts.byId[key].enabled = value.enabled === 'true';
                } else if (key in severityAlerts.byId) {
                  severityAlerts.byId[key].parent_id = value.parent_id;
                  severityAlerts.byId[key].severity = value.severity;
                  severityAlerts.byId[key].enabled = value.enabled === 'true';
                }
              });
              loadRepeatAlertsChainlinkDetails(
                {
                  chain_name: filePath[3],
                  parent_id,
                  alerts: repeatAlerts,
                },
              );
              loadTimeWindowAlertsChainlinkDetails(
                {
                  chain_name: filePath[3],
                  parent_id,
                  alerts: timeWindowAlerts,
                },
              );
              loadThresholdAlertsChainlinkDetails(
                {
                  chain_name: filePath[3],
                  parent_id,
                  alerts: thresholdAlerts,
                },
              );
              loadSeverityAlertsChainlinkDetails(
                {
                  chain_name: filePath[3],
                  parent_id,
                  alerts: severityAlerts,
                },
              );
            }
          }
        } else if (filePath[1] === 'channels') {
          if (filePath[2] === 'email_config.ini') {
            config = await getConfig('channel', 'email_config.ini', '', '');
            Object.values(config.data.result).forEach((value) => {
              const payload = JSON.parse(JSON.stringify(value));
              if (payload.emails_to.length === 0) {
                payload.emails_to = [];
              } else {
                payload.emails_to = payload.emails_to.split(',');
              }
              payload.info = payload.info === 'true';
              payload.warning = payload.warning === 'true';
              payload.critical = payload.critical === 'true';
              payload.error = payload.error === 'true';
              if (payload.parent_ids.length === 0) {
                payload.parent_ids = [];
                payload.parent_names = [];
              } else {
                payload.parent_ids = payload.parent_ids.split(',');
                payload.parent_names = payload.parent_names.split(',');
              }
              addEmailDetails(payload);
            });
          } else if (filePath[2] === 'opsgenie_config.ini') {
            config = await getConfig('channel', 'opsgenie_config.ini', '', '');
            Object.values(config.data.result).forEach((value) => {
              const payload = JSON.parse(JSON.stringify(value));
              payload.info = payload.info === 'true';
              payload.warning = payload.warning === 'true';
              payload.critical = payload.critical === 'true';
              payload.error = payload.error === 'true';
              payload.eu = payload.eu === 'true';
              if (payload.parent_ids.length === 0) {
                payload.parent_ids = [];
                payload.parent_names = [];
              } else {
                payload.parent_ids = payload.parent_ids.split(',');
                payload.parent_names = payload.parent_names.split(',');
              }
              addOpsGenieDetails(payload);
            });
          } else if (filePath[2] === 'pagerduty_config.ini') {
            config = await getConfig('channel', 'pagerduty_config.ini', '', '');
            Object.values(config.data.result).forEach((value) => {
              const payload = JSON.parse(JSON.stringify(value));
              payload.info = payload.info === 'true';
              payload.warning = payload.warning === 'true';
              payload.critical = payload.critical === 'true';
              payload.error = payload.error === 'true';
              if (payload.parent_ids.length === 0) {
                payload.parent_ids = [];
                payload.parent_names = [];
              } else {
                payload.parent_ids = payload.parent_ids.split(',');
                payload.parent_names = payload.parent_names.split(',');
              }
              addPagerDutyDetails(payload);
            });
          } else if (filePath[2] === 'telegram_config.ini') {
            config = await getConfig('channel', 'telegram_config.ini', '', '');
            Object.values(config.data.result).forEach((value) => {
              const payload = JSON.parse(JSON.stringify(value));
              payload.info = payload.info === 'true';
              payload.warning = payload.warning === 'true';
              payload.critical = payload.critical === 'true';
              payload.error = payload.error === 'true';
              payload.alerts = payload.alerts === 'true';
              payload.commands = payload.commands === 'true';
              if (payload.parent_ids.length === 0) {
                payload.parent_ids = [];
                payload.parent_names = [];
              } else {
                payload.parent_ids = payload.parent_ids.split(',');
                payload.parent_names = payload.parent_names.split(',');
              }
              addTelegramDetails(payload);
            });
          } else if (filePath[2] === 'twilio_config.ini') {
            config = await getConfig('channel', 'twilio_config.ini', '', '');
            Object.values(config.data.result).forEach((value) => {
              const payload = JSON.parse(JSON.stringify(value));
              if (payload.twilio_phone_numbers_to_dial_valid.length === 0) {
                payload.twilio_phone_numbers_to_dial_valid = [];
              } else {
                // eslint-disable-next-line max-len
                payload.twilio_phone_numbers_to_dial_valid = payload.twilio_phone_numbers_to_dial_valid.split(
                  ',',
                );
              }
              if (payload.parent_ids.length === 0) {
                payload.parent_ids = [];
                payload.parent_names = [];
              } else {
                payload.parent_ids = payload.parent_ids.split(',');
                payload.parent_names = payload.parent_names.split(',');
              }
              addTwilioDetails(payload);
            });
          } else if (filePath[2] === 'slack_config.ini') {
            config = await getConfig('channel', 'slack_config.ini', '', '');
            Object.values(config.data.result).forEach((value) => {
              const payload = JSON.parse(JSON.stringify(value));
              payload.info = payload.info === 'true';
              payload.warning = payload.warning === 'true';
              payload.critical = payload.critical === 'true';
              payload.error = payload.error === 'true';
              payload.alerts = payload.alerts === 'true';
              payload.commands = payload.commands === 'true';
              if (payload.parent_ids.length === 0) {
                payload.parent_ids = [];
                payload.parent_names = [];
              } else {
                payload.parent_ids = payload.parent_ids.split(',');
                payload.parent_names = payload.parent_names.split(',');
              }
              addSlackDetails(payload);
            });
          }
          // RESET the current chain for all types so when creating a new you
          // chain config you do not attempt to load an old one.
          clearChainIdChainlink();
          clearChainIdSubstrate();
          clearChainIdCosmos();
        }
      }
    } catch (err) {
      ToastsStore.error(
        'An Error occurred your configuration may be corrupted.',
        5000,
      );
    }
  }

  render() {
    return <LoadConfigButton onClick={this.onClick} />;
  }
}

LoadConfig.propTypes = {
  clearChainIdChainlink: PropTypes.func.isRequired,
  clearChainIdSubstrate: PropTypes.func.isRequired,
  clearChainIdCosmos: PropTypes.func.isRequired,
  handleClose: PropTypes.func.isRequired,
  addEmailDetails: PropTypes.func.isRequired,
  addTelegramDetails: PropTypes.func.isRequired,
  addTwilioDetails: PropTypes.func.isRequired,
  addPagerDutyDetails: PropTypes.func.isRequired,
  addOpsGenieDetails: PropTypes.func.isRequired,
  addSlackDetails: PropTypes.func.isRequired,
  addSystemDetails: PropTypes.func.isRequired,
  addDockerHubDetails: PropTypes.func.isRequired,
  addRepositoryDetails: PropTypes.func.isRequired,
  addChainCosmosDetails: PropTypes.func.isRequired,
  addNodeCosmosDetails: PropTypes.func.isRequired,
  addChainSubstrateDetails: PropTypes.func.isRequired,
  addNodeSubstrateDetails: PropTypes.func.isRequired,
  addChainChainlinkDetails: PropTypes.func.isRequired,
  addNodeChainlinkDetails: PropTypes.func.isRequired,
  loadThresholdAlertsGeneralDetails: PropTypes.func.isRequired,
  loadRepeatAlertsCosmosDetails: PropTypes.func.isRequired,
  loadTimeWindowAlertsCosmosDetails: PropTypes.func.isRequired,
  loadThresholdAlertsCosmosDetails: PropTypes.func.isRequired,
  loadSeverityAlertsCosmosDetails: PropTypes.func.isRequired,
  loadRepeatAlertsSubstrateDetails: PropTypes.func.isRequired,
  loadTimeWindowAlertsSubstrateDetails: PropTypes.func.isRequired,
  loadThresholdAlertsSubstrateDetails: PropTypes.func.isRequired,
  loadSeverityAlertsSubstrateDetails: PropTypes.func.isRequired,
  loadRepeatAlertsChainlinkDetails: PropTypes.func.isRequired,
  loadTimeWindowAlertsChainlinkDetails: PropTypes.func.isRequired,
  loadThresholdAlertsChainlinkDetails: PropTypes.func.isRequired,
  loadSeverityAlertsChainlinkDetails: PropTypes.func.isRequired,
  cosmosChains: PropTypes.shape({
    byId: PropTypes.shape({
      repeatAlerts: PropTypes.shape({
        byId: PropTypes.shape({
          name: PropTypes.string,
          warning: PropTypes.shape({
            delay: PropTypes.number,
            repeat: PropTypes.number,
            enabled: PropTypes.bool,
          }),
          critical: PropTypes.shape({
            delay: PropTypes.number,
            repeat: PropTypes.number,
            repeat_enabled: PropTypes.bool,
            enabled: PropTypes.bool,
          }),
          enabled: PropTypes.bool,
        }),
        allIds: [],
      }),
      timeWindowAlerts: PropTypes.shape({
        byId: PropTypes.shape({
          name: PropTypes.string,
          warning: PropTypes.shape({
            threshold: PropTypes.number,
            time_window: PropTypes.number,
            enabled: PropTypes.bool,
          }),
          critical: PropTypes.shape({
            threshold: PropTypes.number,
            time_window: PropTypes.number,
            repeat: PropTypes.number,
            repeat_enabled: PropTypes.bool,
            enabled: PropTypes.bool,
          }),
          enabled: PropTypes.bool,
        }),
        allIds: [],
      }),
      thresholdAlerts: PropTypes.shape({
        byId: PropTypes.shape({
          name: PropTypes.string,
          warning: PropTypes.shape({
            threshold: PropTypes.number,
            enabled: PropTypes.bool,
          }),
          critical: PropTypes.shape({
            threshold: PropTypes.number,
            repeat: PropTypes.number,
            repeat_enabled: PropTypes.bool,
            enabled: PropTypes.bool,
          }),
          enabled: PropTypes.bool,
        }),
        allIds: [],
      }),
      severityAlerts: PropTypes.shape({
        byId: PropTypes.shape({
          name: PropTypes.string,
          severity: PropTypes.string,
          enabled: PropTypes.bool,
        }),
        allIds: [],
      }),
    }).isRequired,
    allIds: [],
  }).isRequired,
  substrateChains: PropTypes.shape({
    byId: PropTypes.shape({
      repeatAlerts: PropTypes.shape({
        byId: PropTypes.shape({
          name: PropTypes.string,
          warning: PropTypes.shape({
            delay: PropTypes.number,
            repeat: PropTypes.number,
            enabled: PropTypes.bool,
          }),
          critical: PropTypes.shape({
            delay: PropTypes.number,
            repeat: PropTypes.number,
            repeat_enabled: PropTypes.bool,
            enabled: PropTypes.bool,
          }),
          enabled: PropTypes.bool,
        }),
        allIds: [],
      }),
      timeWindowAlerts: PropTypes.shape({
        byId: PropTypes.shape({
          name: PropTypes.string,
          warning: PropTypes.shape({
            threshold: PropTypes.number,
            time_window: PropTypes.number,
            enabled: PropTypes.bool,
          }),
          critical: PropTypes.shape({
            threshold: PropTypes.number,
            time_window: PropTypes.number,
            repeat: PropTypes.number,
            repeat_enabled: PropTypes.bool,
            enabled: PropTypes.bool,
          }),
          enabled: PropTypes.bool,
        }),
        allIds: [],
      }),
      thresholdAlerts: PropTypes.shape({
        byId: PropTypes.shape({
          name: PropTypes.string,
          warning: PropTypes.shape({
            threshold: PropTypes.number,
            enabled: PropTypes.bool,
          }),
          critical: PropTypes.shape({
            threshold: PropTypes.number,
            repeat: PropTypes.number,
            repeat_enabled: PropTypes.bool,
            enabled: PropTypes.bool,
          }),
          enabled: PropTypes.bool,
        }),
        allIds: [],
      }),
      severityAlerts: PropTypes.shape({
        byId: PropTypes.shape({
          name: PropTypes.string,
          severity: PropTypes.string,
          enabled: PropTypes.bool,
        }),
        allIds: [],
      }),
    }).isRequired,
    allIds: [],
  }).isRequired,
  chainlinkChains: PropTypes.shape({
    byId: PropTypes.shape({
      repeatAlerts: PropTypes.shape({
        byId: PropTypes.shape({
          name: PropTypes.string,
          warning: PropTypes.shape({
            delay: PropTypes.number,
            repeat: PropTypes.number,
            enabled: PropTypes.bool,
          }),
          critical: PropTypes.shape({
            delay: PropTypes.number,
            repeat: PropTypes.number,
            repeat_enabled: PropTypes.bool,
            enabled: PropTypes.bool,
          }),
          enabled: PropTypes.bool,
        }),
        allIds: [],
      }),
      timeWindowAlerts: PropTypes.shape({
        byId: PropTypes.shape({
          name: PropTypes.string,
          warning: PropTypes.shape({
            threshold: PropTypes.number,
            time_window: PropTypes.number,
            enabled: PropTypes.bool,
          }),
          critical: PropTypes.shape({
            threshold: PropTypes.number,
            time_window: PropTypes.number,
            repeat: PropTypes.number,
            enabled: PropTypes.bool,
          }),
          enabled: PropTypes.bool,
        }),
        allIds: [],
      }),
      thresholdAlerts: PropTypes.shape({
        byId: PropTypes.shape({
          name: PropTypes.string,
          warning: PropTypes.shape({
            threshold: PropTypes.number,
            enabled: PropTypes.bool,
          }),
          critical: PropTypes.shape({
            threshold: PropTypes.number,
            repeat: PropTypes.number,
            repeat_enabled: PropTypes.bool,
            enabled: PropTypes.bool,
          }),
          enabled: PropTypes.bool,
        }),
        allIds: [],
      }),
      severityAlerts: PropTypes.shape({
        byId: PropTypes.shape({
          name: PropTypes.string,
          severity: PropTypes.string,
          enabled: PropTypes.bool,
        }),
        allIds: [],
      }),
    }).isRequired,
    allIds: [],
  }).isRequired,
};

export default connect(mapStateToProps, mapDispatchToProps)(LoadConfig);
