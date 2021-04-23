/* eslint-disable no-multi-assign */
/* eslint-disable max-len */
/* eslint-disable no-await-in-loop */
/* eslint-disable camelcase */
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
} from 'redux/actions/channelActions';
import {
  addDocker,
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
} from 'redux/actions/cosmosActions';
import {
  addNodeSubstrate,
  addChainSubstrate,
  loadRepeatAlertsSubstrate,
  loadTimeWindowAlertsSubstrate,
  loadThresholdAlertsSubstrate,
  loadSeverityAlertsSubstrate,
} from 'redux/actions/substrateActions';
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

  substrateChains: state.SubstrateChainsReducer,
  substrateNodes: state.SubstrateNodesReducer,

  // Channels related data
  emails: state.EmailsReducer,
  opsgenies: state.OpsGenieReducer,
  pagerduties: state.PagerDutyReducer,
  telegrams: state.TelegramsReducer,
  twilios: state.TwiliosReducer,
  slacks: state.SlacksReducer,

  // General data related to
  repositories: state.RepositoryReducer,
  kmses: state.KmsReducer,
  general: state.GeneralReducer.byId[GENERAL],
  systems: state.SystemsReducer,
  periodic: state.PeriodicReducer,
});

function mapDispatchToProps(dispatch) {
  return {
    addEmailDetails: (details) => dispatch(addEmail(details)),
    addTelegramDetails: (details) => dispatch(addTelegram(details)),
    addTwilioDetails: (details) => dispatch(addTwilio(details)),
    addPagerDutyDetails: (details) => dispatch(addPagerDuty(details)),
    addOpsGenieDetails: (details) => dispatch(addOpsGenie(details)),
    addChainCosmosDetails: (details) => dispatch(addChainCosmos(details)),
    addNodeCosmosDetails: (details) => dispatch(addNodeCosmos(details)),
    addChainSubstrateDetails: (details) => dispatch(addChainSubstrate(details)),
    addSystemDetails: (details) => dispatch(addSystem(details)),
    addDockerDetails: (details) => dispatch(addDocker(details)),
    addRepositoryDetails: (details) => dispatch(addRepository(details)),
    addNodeSubstrateDetails: (details) => dispatch(addNodeSubstrate(details)),
    loadThresholdAlertsGeneralDetails: (details) => dispatch(loadThresholdAlertsGeneral(details)),
    loadRepeatAlertsCosmosDetails: (details) => dispatch(loadRepeatAlertsCosmos(details)),
    loadTimeWindowAlertsCosmosDetails: (details) => dispatch(loadTimeWindowAlertsCosmos(details)),
    loadThresholdAlertsCosmosDetails: (details) => dispatch(loadThresholdAlertsCosmos(details)),
    loadSeverityAlertsCosmosDetails: (details) => dispatch(loadSeverityAlertsCosmos(details)),
    loadRepeatAlertsSubstrateDetails: (details) => dispatch(loadRepeatAlertsSubstrate(details)),
    loadTimeWindowAlertsSubstrateDetails: (details) => dispatch(loadTimeWindowAlertsSubstrate(details)),
    loadThresholdAlertsSubstrateDetails: (details) => dispatch(loadThresholdAlertsSubstrate(details)),
    loadSeverityAlertsSubstrateDetails: (details) => dispatch(loadSeverityAlertsSubstrate(details)),
  };
}

// Checking if the current chain has been setup and if not set it up
function CreateChain(config, chainName, chainState, addChain) {
  const singleConfig = config[Object.keys(config)[0]];

  if (!(singleConfig.parent_id in chainState.byId) && !(chainState.allIds.includes(singleConfig.parent_id))) {
    addChain({ id: singleConfig.parent_id, chain_name: chainName });
  }
}

class LoadConfig extends Component {
  constructor(props) {
    super(props);
    this.loadConfigs = this.loadConfigs.bind(this);
  }

  async loadConfigs() {
    const {
      addEmailDetails,
      addTelegramDetails,
      addTwilioDetails,
      addPagerDutyDetails,
      addOpsGenieDetails,
      addDockerDetails,
      addSystemDetails,
      addRepositoryDetails,
      addChainCosmosDetails,
      addChainSubstrateDetails,
      cosmosChains,
      addNodeCosmosDetails,
      substrateChains,
      addNodeSubstrateDetails,
      loadThresholdAlertsGeneralDetails,
      loadRepeatAlertsCosmosDetails,
      loadTimeWindowAlertsCosmosDetails,
      loadThresholdAlertsCosmosDetails,
      loadSeverityAlertsCosmosDetails,
      loadRepeatAlertsSubstrateDetails,
      loadTimeWindowAlertsSubstrateDetails,
      loadThresholdAlertsSubstrateDetails,
      loadSeverityAlertsSubstrateDetails,
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
          if (filePath[2] === 'repos_config.ini') {
            config = await getConfig('general', 'repos_config.ini', '', '');
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
          } else if (filePath[2] === 'dockers_config.ini') {
            config = await getConfig('general', 'dockers_config.ini', '', '');
            Object.values(config.data.result).forEach((value) => {
              const payload = JSON.parse(JSON.stringify(value));
              payload.monitor_docker = payload.monitor_docker === 'true';
              addDockerDetails(payload);
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
            if (filePath[4] === 'repos_config.ini') {
              config = await getConfig('chain', 'repos_config.ini', filePath[3], 'cosmos');
              CreateChain(config.data.result, filePath[3], cosmosChains, addChainCosmosDetails);
              Object.values(config.data.result).forEach((value) => {
                const payload = JSON.parse(JSON.stringify(value));
                payload.monitor_repo = payload.monitor_repo === 'true';
                addRepositoryDetails(payload);
              });
            } else if (filePath[4] === 'dockers_config.ini') {
              config = await getConfig('chain', 'dockers_config.ini', filePath[3], 'cosmos');
              CreateChain(config.data.result, filePath[3], cosmosChains, addChainCosmosDetails);
              Object.values(config.data.result).forEach((value) => {
                const payload = JSON.parse(JSON.stringify(value));
                payload.monitor_docker = payload.monitor_docker === 'true';
                addDockerDetails(payload);
              });
            } else if (filePath[4] === 'nodes_config.ini') {
              config = await getConfig('chain', 'nodes_config.ini', filePath[3], 'cosmos');
              CreateChain(config.data.result, filePath[3], cosmosChains, addChainCosmosDetails);
              Object.values(config.data.result).forEach((value) => {
                const node = JSON.parse(JSON.stringify(value));
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
              CreateChain(config.data.result, filePath[3], cosmosChains, addChainCosmosDetails);
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
              loadRepeatAlertsCosmosDetails({ chain_name: filePath[3], parent_id, alerts: repeatAlerts });
              loadTimeWindowAlertsCosmosDetails({ chain_name: filePath[3], parent_id, alerts: timeWindowAlerts });
              loadThresholdAlertsCosmosDetails({ chain_name: filePath[3], parent_id, alerts: thresholdAlerts });
              loadSeverityAlertsCosmosDetails({ chain_name: filePath[3], parent_id, alerts: severityAlerts });
            }
          } else if (filePath[2] === 'substrate') {
            if (filePath[4] === 'repos_config.ini') {
              config = await getConfig('chain', 'repos_config.ini', filePath[3], 'substrate');
              CreateChain(config.data.result, filePath[3], substrateChains, addChainSubstrateDetails);
              Object.values(config.data.result).forEach((value) => {
                const payload = JSON.parse(JSON.stringify(value));
                payload.monitor_repo = payload.monitor_repo === 'true';
                addRepositoryDetails(payload);
              });
            } else if (filePath[4] === 'dockers_config.ini') {
              config = await getConfig('chain', 'dockers_config.ini', filePath[3], 'substrate');
              CreateChain(config.data.result, filePath[3], substrateChains, addChainSubstrateDetails);
              Object.values(config.data.result).forEach((value) => {
                const payload = JSON.parse(JSON.stringify(value));
                payload.monitor_docker = payload.monitor_docker === 'true';
                addDockerDetails(payload);
              });
            } else if (filePath[4] === 'nodes_config.ini') {
              config = await getConfig('chain', 'nodes_config.ini', filePath[3], 'substrate');
              CreateChain(config.data.result, filePath[3], substrateChains, addChainSubstrateDetails);
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
              CreateChain(config.data.result, filePath[3], substrateChains, addChainSubstrateDetails);
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
              loadRepeatAlertsSubstrateDetails({ chain_name: filePath[3], parent_id, alerts: repeatAlerts });
              loadTimeWindowAlertsSubstrateDetails({ chain_name: filePath[3], parent_id, alerts: timeWindowAlerts });
              loadThresholdAlertsSubstrateDetails({ chain_name: filePath[3], parent_id, alerts: thresholdAlerts });
              loadSeverityAlertsSubstrateDetails({ chain_name: filePath[3], parent_id, alerts: severityAlerts });
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
              payload.eu = payload.eu = 'true';
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
                payload.twilio_phone_numbers_to_dial_valid = payload.twilio_phone_numbers_to_dial_valid.split(
                  ',',
                );
              }
              console.log(payload);
              console.log(payload.parent_ids.length);
              if (payload.parent_ids.length === 0) {
                payload.parent_ids = [];
                payload.parent_names = [];
              } else {
                payload.parent_ids = payload.parent_ids.split(',');
                payload.parent_names = payload.parent_names.split(',');
              }
              console.log(payload);
              addTwilioDetails(payload);
            });
          }
        }
      }
    } catch (err) {
      console.log(err);
      ToastsStore.error(
        'An Error occurred your configuration may be corrupted.',
        5000,
      );
    }
  }

  render() {
    return <LoadConfigButton onClick={this.loadConfigs} />;
  }
}

LoadConfig.propTypes = {
  addEmailDetails: PropTypes.func.isRequired,
  addTelegramDetails: PropTypes.func.isRequired,
  addTwilioDetails: PropTypes.func.isRequired,
  addPagerDutyDetails: PropTypes.func.isRequired,
  addOpsGenieDetails: PropTypes.func.isRequired,
  addSystemDetails: PropTypes.func.isRequired,
  addDockerDetails: PropTypes.func.isRequired,
  addRepositoryDetails: PropTypes.func.isRequired,
  addChainCosmosDetails: PropTypes.func.isRequired,
  addNodeCosmosDetails: PropTypes.func.isRequired,
  addChainSubstrateDetails: PropTypes.func.isRequired,
  addNodeSubstrateDetails: PropTypes.func.isRequired,
  loadThresholdAlertsGeneralDetails: PropTypes.func.isRequired,
  loadRepeatAlertsCosmosDetails: PropTypes.func.isRequired,
  loadTimeWindowAlertsCosmosDetails: PropTypes.func.isRequired,
  loadThresholdAlertsCosmosDetails: PropTypes.func.isRequired,
  loadSeverityAlertsCosmosDetails: PropTypes.func.isRequired,
  loadRepeatAlertsSubstrateDetails: PropTypes.func.isRequired,
  loadTimeWindowAlertsSubstrateDetails: PropTypes.func.isRequired,
  loadThresholdAlertsSubstrateDetails: PropTypes.func.isRequired,
  loadSeverityAlertsSubstrateDetails: PropTypes.func.isRequired,
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
            timewindow: PropTypes.number,
            enabled: PropTypes.bool,
          }),
          critical: PropTypes.shape({
            threshold: PropTypes.number,
            timewindow: PropTypes.number,
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
            timewindow: PropTypes.number,
            enabled: PropTypes.bool,
          }),
          critical: PropTypes.shape({
            threshold: PropTypes.number,
            timewindow: PropTypes.number,
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
