import React, { Component } from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { ToastsStore } from 'react-toasts';
import { LoadConfigButton } from 'utils/buttons';
import { getConfigPaths, getConfig } from 'utils/data';
import { GLOBAL } from 'constants/constants';
import {
  loadTelegram, loadTwilio, loadEmail, loadPagerduty,
  loadOpsgenie, 
} from 'redux/actions/channelActions';
import {
  loadNodeCosmos, loadReposCosmos, loadKMSCosmos,
  loadRepeatAlertsCosmos, loadTimeWindowAlertsCosmos, loadThresholdAlertsCosmos,
  loadSeverityAlertsCosmos,
} from 'redux/actions/cosmosActions';
import {
  loadRepository, loadReposGeneral, loadKMS, loadSystemGeneral,
  loadRepeatAlertsGeneral, loadThresholdAlertsGeneral, updatePeriodic,
  loadSystem,
} from 'redux/actions/generalActions';
import {
  loadNodeSubstrate, loadReposSubstrate, loadRepeatAlertsSubstrate,
  loadTimeWindowAlertsSubstrate, loadThresholdAlertsSubstrate,
  loadSeverityAlertsSubstrate,
} from 'redux/actions/substrateActions';
import {
  cosmosRepeatAlerts, cosmosThresholdAlerts, cosmosTimeWindowAlerts,
  cosmosSeverityAlerts,
} from 'redux/reducers/cosmosChainsReducer';
import {
  substrateRepeatAlerts, substrateThresholdAlerts, substrateTimeWindowAlerts,
  substrateSeverityAlerts,
} from 'redux/reducers/substrateChainsReducer';
import { generalThresholdAlerts, generalRepeatAlerts,
} from 'redux/reducers/generalReducer';

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

  // General data related to
  repositories: state.RepositoryReducer,
  kmses: state.KmsReducer,
  general: state.GeneralReducer.byId[GLOBAL],
  systems: state.SystemsReducer,
  periodic: state.PeriodicReducer,
});

function mapDispatchToProps(dispatch) {
  return {
    loadTelegramDetails: (details) => dispatch(loadTelegram(details)),
    loadTwilioDetails: (details) => dispatch(loadTwilio(details)),
    loadEmailDetails: (details) => dispatch(loadEmail(details)),
    loadPagerdutyDetails: (details) => dispatch(loadPagerduty(details)),
    loadOpsgenieDetails: (details) => dispatch(loadOpsgenie(details)),

    loadRepositoryDetails: (details) => dispatch(loadRepository(details)),
    loadSystemDetails: (details) => dispatch(loadSystem(details)),
    loadKMSDetails: (details) => dispatch(loadKMS(details)), 

    loadNodeCosmosDetails: (details) => dispatch(loadNodeCosmos(details)),
    loadReposCosmosDetails: (details) => dispatch(loadReposCosmos(details)),
    loadKMSCosmosDetails: (details) => dispatch(loadKMSCosmos(details)),
    loadRepeatAlertsCosmosDetails: (details) =>
      dispatch(loadRepeatAlertsCosmos(details)),
    loadTimeWindowAlertsCosmosDetails: (details) =>
      dispatch(loadTimeWindowAlertsCosmos(details)),
    loadThresholdAlertsCosmosDetails: (details) =>
      dispatch(loadThresholdAlertsCosmos(details)),
    loadSeverityAlertsCosmosDetails: (details) =>
      dispatch(loadSeverityAlertsCosmos(details)),
  
    loadNodeSubstrateDetails: (details) => dispatch(loadNodeSubstrate(details)),
    loadReposSubstrateDetails: (details) =>
      dispatch(loadReposSubstrate(details)),
    loadRepeatAlertsSubstrateDetails: (details) =>
      dispatch(loadRepeatAlertsSubstrate(details)),
    loadTimeWindowAlertsSubstrateDetails: (details) =>
      dispatch(loadTimeWindowAlertsSubstrate(details)),
    loadThresholdAlertsSubstrateDetails: (details) =>
      dispatch(loadThresholdAlertsSubstrate(details)),
    loadSeverityAlertsSubstrateDetails: (details) =>
      dispatch(loadSeverityAlertsSubstrate(details)),
  
    loadReposGeneralDetails: (details) =>
      dispatch(loadReposGeneral(details)),
    loadSystemGeneralDetails: (details) =>
      dispatch(loadSystemGeneral(details)),
    loadRepeatAlertsGeneralDetails: (details) =>
      dispatch(loadRepeatAlertsGeneral(details)),
    loadThresholdAlertsGeneralDetails: (details) =>
      dispatch(loadThresholdAlertsGeneral(details)),
    updatePeriodicDetails: (details) => dispatch(updatePeriodic(details)),
  };
}

class LoadConfig extends Component {
  constructor(props) {
    super(props);
    this.loadConfigs = this.loadConfigs.bind(this);
  }

  async loadConfigs() {
    const {
      loadTelegramDetails, loadTwilioDetails, loadEmailDetails,
      loadPagerdutyDetails, loadOpsgenieDetails, loadNodeCosmosDetails,
      loadReposCosmosDetails, loadRepositoryDetails, loadKMSCosmosDetails,
      loadKMSDetails, loadRepeatAlertsCosmosDetails, loadSystemDetails,
      loadTimeWindowAlertsCosmosDetails, loadThresholdAlertsCosmosDetails,
      loadSeverityAlertsCosmosDetails, loadReposGeneralDetails,
      loadSystemGeneralDetails, loadRepeatAlertsGeneralDetails,
      loadThresholdAlertsGeneralDetails, loadNodeSubstrateDetails,
      loadReposSubstrateDetails, loadRepeatAlertsSubstrateDetails,
      loadTimeWindowAlertsSubstrateDetails, loadThresholdAlertsSubstrateDetails,
      loadSeverityAlertsSubstrateDetails, updatePeriodicDetails, handleClose,
    } = this.props;

    ToastsStore.info('Attempting to Load Configuration.', 5000);
    const paths = await getConfigPaths();
    const files = paths.data.result;
    let config = {}
    let node = {}
    let repo = {}
    let kms = {}
    let repeatAlerts = {}
    let thresholdAlerts = {}
    let timeWindowAlerts = {}
    let severityAlerts = {}
    let payload = {}
    let warning = {}
    let critical = {}
    let parent_id = ''
    try {
      for (var i = 0; i < files.length; i++) {
        var res = files[i].split("/");
        if (res[1] === 'general') {
          if (res[2] === 'periodic_config.ini') {
            config = await getConfig('general', 'periodic_config.ini', '', '');
            payload = JSON.parse(JSON.stringify(config.data.result));
            payload.periodic.enabled = (payload.periodic.enabled  === 'true');
            updatePeriodicDetails(payload.periodic);
          }else if (res[2] === 'repos_config.ini') {
            config = await getConfig('general', 'repos_config.ini', '', '');
            // eslint-disable-next-line 
            Object.keys(config.data.result).forEach(function(key) {
              payload = JSON.parse(JSON.stringify(config.data.result[key]));
              payload.monitor_repo = (payload.monitor_repo  === 'true');
              loadRepositoryDetails(payload);
              loadReposGeneralDetails(payload);
            });
          }else if (res[2] === 'systems_config.ini') {
            config = await getConfig('general', 'systems_config.ini', '', '');
            // eslint-disable-next-line 
            Object.keys(config.data.result).forEach(function(key) {
              payload = JSON.parse(JSON.stringify(config.data.result[key]));
              payload.monitor_system = (payload.monitor_system  === 'true');
              loadSystemDetails(payload);
              loadSystemGeneralDetails(payload);
            });
          }else if (res[2] === 'alerts_config.ini') {
            config = await getConfig('general', 'alerts_config.ini', '', '');
            // Create copies of alerts
            repeatAlerts = JSON.parse(JSON.stringify(generalRepeatAlerts));
            thresholdAlerts = JSON.parse(JSON.stringify(
              generalThresholdAlerts));
            // eslint-disable-next-line 
            Object.keys(config.data.result).forEach(function(key) {
              parent_id = config.data.result[key].parent_id;
              if (key in repeatAlerts.byId) {
                repeatAlerts.byId[key].parent_id = config.data.result[key]
                  .parent_id;
                warning = {
                  repeat: config.data.result[key].warning_repeat,
                  enabled: (config.data.result[key].warning_enabled === 'true'),
                }
                critical = {
                  repeat: config.data.result[key].critical_repeat,
                  enabled: (config.data.result[key].critical_enabled ===
                    'true'),
                }
                repeatAlerts.byId[key].warning = warning;
                repeatAlerts.byId[key].critical = critical;
                repeatAlerts.byId[key].enabled = (
                  config.data.result[key].enabled === 'true');
              }else if (key in thresholdAlerts.byId) {
                thresholdAlerts.byId[key].parent_id = config.data.result[key]
                  .parent_id;
                warning = {
                  threshold: config.data.result[key].warning_threshold,
                  enabled: (config.data.result[key].warning_enabled === 'true'),
                }
                critical = {
                  threshold: config.data.result[key].critical_threshold,
                  repeat: config.data.result[key].critical_repeat,
                  enabled: (config.data.result[key].critical_enabled ===
                    'true'),
                }
                thresholdAlerts.byId[key].warning = warning;
                thresholdAlerts.byId[key].critical = critical;
                thresholdAlerts.byId[key].enabled = (config.data.result[key]
                  .enabled === 'true');
              }
            });
            payload = { parent_id: parent_id, alerts: repeatAlerts }
            loadRepeatAlertsGeneralDetails(payload);
            payload = { parent_id: parent_id, alerts: thresholdAlerts }
            loadThresholdAlertsGeneralDetails(payload);
          }
        }else if (res[1] === 'channels') {
          if (res[2] === 'email_config.ini') {
            config = await getConfig('channel', 'email_config.ini', '', '');
            // eslint-disable-next-line 
            Object.keys(config.data.result).forEach(function(key) {
              payload = JSON.parse(JSON.stringify(config.data.result[key]));
              if (payload.emails_to.length === 0){
                payload.emails_to = [];
              }else {
                payload.emails_to = payload.emails_to.split(',');
              }
              payload.info = (payload.info  === 'true');
              payload.warning = (payload.warning  === 'true');
              payload.critical = (payload.critical  === 'true');
              payload.error = (payload.error  === 'true');
              if (payload.parent_ids.length === 0){
                payload.parent_ids = [];
                payload.parent_names = [];
              }else {
                payload.parent_ids = payload.parent_ids.split(',');
                payload.parent_names = payload.parent_names.split(',');
              }
              loadEmailDetails(payload);
            });
          }else if (res[2] === 'opsgenie_config.ini') {
            config = await getConfig('channel', 'opsgenie_config.ini', '', '');
            // eslint-disable-next-line 
            Object.keys(config.data.result).forEach(function(key) {
              payload = JSON.parse(JSON.stringify(config.data.result[key]));
              payload.info = (payload.info  === 'true');
              payload.warning = (payload.warning  === 'true');
              payload.critical = (payload.critical  === 'true');
              payload.error = (payload.error  === 'true');
              payload.eu = (payload.eu = 'true');
              if (payload.parent_ids.length === 0){
                payload.parent_ids = [];
                payload.parent_names = [];
              }else {
                payload.parent_ids = payload.parent_ids.split(',');
                payload.parent_names = payload.parent_names.split(',');
              }
              loadOpsgenieDetails(payload);
            });
          }else if (res[2] === 'pagerduty_config.ini') {
            config = await getConfig('channel', 'pagerduty_config.ini', '', '');
            // eslint-disable-next-line 
            Object.keys(config.data.result).forEach(function(key) {
              payload = JSON.parse(JSON.stringify(config.data.result[key]));
              payload.info = (payload.info  === 'true');
              payload.warning = (payload.warning  === 'true');
              payload.critical = (payload.critical  === 'true');
              payload.error = (payload.error  === 'true');
              if (payload.parent_ids.length === 0){
                payload.parent_ids = [];
                payload.parent_names = [];
              }else {
                payload.parent_ids = payload.parent_ids.split(',');
                payload.parent_names = payload.parent_names.split(',');
              }
              loadPagerdutyDetails(payload);
            });
          }else if (res[2] === 'telegram_config.ini') {
            config = await getConfig('channel', 'telegram_config.ini', '', '');
            // eslint-disable-next-line 
            Object.keys(config.data.result).forEach(function(key) {
              payload = JSON.parse(JSON.stringify(config.data.result[key]));
              payload.info = (payload.info  === 'true');
              payload.warning = (payload.warning  === 'true');
              payload.critical = (payload.critical  === 'true');
              payload.error = (payload.error  === 'true');
              payload.alerts = (payload.alerts === 'true');
              payload.commands = (payload.commands === 'true');
              if (payload.parent_ids.length === 0){
                payload.parent_ids = [];
                payload.parent_names = [];
              }else {
                payload.parent_ids = payload.parent_ids.split(',');
                payload.parent_names = payload.parent_names.split(',');
              }
              loadTelegramDetails(payload);
            });
          }else if (res[2] === 'twilio_config.ini') {
            config = await getConfig('channel', 'twilio_config.ini', '', '');
            // eslint-disable-next-line 
            Object.keys(config.data.result).forEach(function(key) {
              payload = JSON.parse(JSON.stringify(config.data.result[key]));
              if (payload.twilio_phone_numbers_to_dial.length === 0){
                payload.twilio_phone_numbers_to_dial = [];
              }else {
                payload.twilio_phone_numbers_to_dial = payload
                  .twilio_phone_numbers_to_dial.split(',');
              }
              if (payload.parent_ids.length === 0){
                payload.parent_ids = [];
                payload.parent_names = [];
              }else {
                payload.parent_ids = payload.parent_ids.split(',');
                payload.parent_names = payload.parent_names.split(',');
              }
              loadTwilioDetails(payload);
            });
          }
        } else if (res[1] === 'chains') {
          if (res[2] === 'cosmos'){
            if (res[4] === 'nodes_config.ini') {
              config = await getConfig('chain', 'nodes_config.ini', res[3],
                'cosmos');
              // eslint-disable-next-line 
              Object.keys(config.data.result).forEach(function(key) {
                node = JSON.parse(JSON.stringify(config.data.result[key]));
                node.is_archive_node = (node.is_archive_node  === 'true');
                node.is_validator = (node.is_validator === 'true');
                node.monitor_node = (node.monitor_node === 'true');
                node.use_as_data_source = (node.use_as_data_source === 'true');
                payload = {
                  chain_name: res[3],
                  node: node,
                }
                loadNodeCosmosDetails(payload);
              });
            } else if (res[4] === 'repos_config.ini') {
              config = await getConfig('chain', 'repos_config.ini', res[3],
                'cosmos');
              // eslint-disable-next-line 
              Object.keys(config.data.result).forEach(function(key) {
                repo = JSON.parse(JSON.stringify(config.data.result[key]));
                repo.monitor_repo = (repo.monitor_repo  === 'true');
                loadRepositoryDetails(repo);
                payload = { chain_name: res[3], repo: repo }
                loadReposCosmosDetails(payload);
              });
            } else if (res[4] === 'kms_config.ini') {
              config = await getConfig('chain', 'kms_config.ini', res[3],
                'cosmos');
              // eslint-disable-next-line 
              Object.keys(config.data.result).forEach(function(key) {
                kms = JSON.parse(JSON.stringify(config.data.result[key]));
                kms.monitor_kms = (kms.monitor_kms  === 'true');
                loadKMSDetails(kms);
                payload = { chain_name: res[3], kms: kms }
                loadKMSCosmosDetails(payload);
              });
            } else if (res[4] === 'alerts_config.ini') {
              config = await getConfig('chain', 'alerts_config.ini', res[3],
                'cosmos');
              // Create copies of alerts
              repeatAlerts = JSON.parse(JSON.stringify(
                cosmosRepeatAlerts));
              thresholdAlerts = JSON.parse(JSON.stringify(
                cosmosThresholdAlerts));
              timeWindowAlerts = JSON.parse(JSON.stringify(
                cosmosTimeWindowAlerts));
              severityAlerts = JSON.parse(JSON.stringify(
                cosmosSeverityAlerts));
              // eslint-disable-next-line 
              Object.keys(config.data.result).forEach(function(key) {
                parent_id = config.data.result[key].parent_id;
                if (key in repeatAlerts.byId) {
                  repeatAlerts.byId[key].parent_id = config.data.result[key]
                    .parent_id;
                  warning = {
                    repeat: config.data.result[key].warning_repeat,
                    enabled: (config.data.result[key].warning_enabled ===
                        'true'),
                  }
                  critical = {
                    repeat: config.data.result[key].critical_repeat,
                    enabled: (config.data.result[key].critical_enabled ===
                      'true'),
                  }
                  repeatAlerts.byId[key].warning = warning;
                  repeatAlerts.byId[key].critical = critical;
                  repeatAlerts.byId[key].enabled = (config.data.result[key]
                    .enabled === 'true');
                }else if (key in thresholdAlerts.byId) {
                  thresholdAlerts.byId[key].parent_id = config.data.result[key]
                    .parent_id;
                  warning = {
                    threshold: config.data.result[key].warning_threshold,
                    enabled: (config.data.result[key].warning_enabled === 
                      'true'),
                  }
                  critical = {
                    threshold: config.data.result[key].critical_threshold,
                    repeat: config.data.result[key].critical_repeat,
                    enabled: (config.data.result[key].critical_enabled ===
                      'true'),
                  }
                  thresholdAlerts.byId[key].warning = warning;
                  thresholdAlerts.byId[key].critical = critical;
                  thresholdAlerts.byId[key].enabled = (config.data.result[key]
                    .enabled === 'true');
                }else if (key in timeWindowAlerts.byId) {
                  timeWindowAlerts.byId[key].parent_id = config.data
                    .result[key].parent_id;
                  warning = {
                    threshold: config.data.result[key].warning_threshold,
                    time_window: config.data.result[key].warning_time_window,
                    enabled: (config.data.result[key].warning_enabled ===
                        'true'),
                  }
                  critical = {
                    threshold: config.data.result[key].critical_threshold,
                    time_window: config.data.result[key].critical_time_window,
                    enabled: (config.data.result[key].critical_enabled ===
                      'true'),
                  }
                  timeWindowAlerts.byId[key].warning = warning;
                  timeWindowAlerts.byId[key].critical = critical;
                  timeWindowAlerts.byId[key].enabled = (config.data.result[key]
                    .enabled === 'true');
                }else if (key in severityAlerts.byId) {
                  severityAlerts.byId[key].parent_id = config.data.result[key]
                    .parent_id;
                  severityAlerts.byId[key].severity = config.data.result[key]
                    .severity;
                  severityAlerts.byId[key].enabled = (config.data.result[key]
                    .enabled === 'true');
                }
              });
              payload = {
                chain_name: res[3],
                parent_id: parent_id,
                alerts: repeatAlerts,
              }
              loadRepeatAlertsCosmosDetails(payload);
              payload = {
                chain_name: res[3],
                parent_id: parent_id,
                alerts: timeWindowAlerts,
              }
              loadTimeWindowAlertsCosmosDetails(payload);
              payload = {
                chain_name: res[3],
                parent_id: parent_id,
                alerts: thresholdAlerts,
              }
              loadThresholdAlertsCosmosDetails(payload);
              payload = {
                chain_name: res[3],
                parent_id: parent_id,
                alerts: severityAlerts,
              }
              loadSeverityAlertsCosmosDetails(payload);
            }
          } else if (res[2] === 'substrate') {
            if (res[4] === 'nodes_config.ini') {
              config = await getConfig('chain', 'nodes_config.ini', res[3],
                'substrate');
              // eslint-disable-next-line 
              Object.keys(config.data.result).forEach(function(key) {
                node = JSON.parse(JSON.stringify(config.data.result[key]));
                node.is_archive_node = (node.is_archive_node  === 'true');
                node.is_validator = (node.is_validator === 'true');
                node.monitor_node = (node.monitor_node === 'true');
                node.use_as_data_source = (node.use_as_data_source === 'true');
                payload = {
                  chain_name: res[3],
                  node: node,
                }
                loadNodeSubstrateDetails(payload);
              });
            } else if (res[4] === 'repos_config.ini') {
              config = await getConfig('chain', 'repos_config.ini', res[3],
                'substrate');
              // eslint-disable-next-line 
              Object.keys(config.data.result).forEach(function(key) {
                repo = JSON.parse(JSON.stringify(config.data.result[key]));
                repo.monitor_repo = (repo.monitor_repo  === 'true');
                payload = {
                  chain_name: res[3],
                  repo: repo,
                }
                loadRepositoryDetails(repo);
                loadReposSubstrateDetails(payload);
              });
            } else if (res[4] === 'alerts_config.ini') {
              config = await getConfig('chain', 'alerts_config.ini', res[3],
                'substrate');
              // Create copies of alerts
              repeatAlerts = JSON.parse(JSON.stringify(
                substrateRepeatAlerts));
              thresholdAlerts = JSON.parse(JSON.stringify(
                substrateThresholdAlerts));
              timeWindowAlerts = JSON.parse(JSON.stringify(
                substrateTimeWindowAlerts));
              severityAlerts = JSON.parse(JSON.stringify(
                substrateSeverityAlerts));
              // eslint-disable-next-line 
              Object.keys(config.data.result).forEach(function(key) {
                parent_id = config.data.result[key].parent_id;
                if (key in repeatAlerts.byId) {
                  repeatAlerts.byId[key].parent_id = config.data.result[key]
                    .parent_id;
                  warning = {
                    repeat: config.data.result[key].warning_repeat,
                    enabled: (config.data.result[key].warning_enabled === 
                      'true'),
                  }
                  critical = {
                    repeat: config.data.result[key].critical_repeat,
                    enabled: (config.data.result[key].critical_enabled ===
                      'true'),
                  }
                  repeatAlerts.byId[key].warning = warning;
                  repeatAlerts.byId[key].critical = critical;
                  repeatAlerts.byId[key].enabled = (config.data.result[key]
                    .enabled === 'true');
                }else if (key in thresholdAlerts.byId) {
                  thresholdAlerts.byId[key].parent_id = config.data.result[key]
                    .parent_id;
                  warning = {
                    threshold: config.data.result[key].warning_threshold,
                    enabled: (config.data.result[key].warning_enabled ===
                      'true'),
                  }
                  critical = {
                    threshold: config.data.result[key].critical_threshold,
                    repeat: config.data.result[key].critical_repeat,
                    enabled: (config.data.result[key].critical_enabled ===
                      'true'),
                  }
                  thresholdAlerts.byId[key].warning = warning;
                  thresholdAlerts.byId[key].critical = critical;
                  thresholdAlerts.byId[key].enabled = (config.data.result[key]
                    .enabled === 'true');
                }else if (key in timeWindowAlerts.byId) {
                  timeWindowAlerts.byId[key].parent_id = config.data
                    .result[key].parent_id;
                  warning = {
                    threshold: config.data.result[key].warning_threshold,
                    time_window: config.data.result[key].warning_time_window,
                    enabled: (config.data.result[key].warning_enabled ===
                      'true'),
                  }
                  critical = {
                    threshold: config.data.result[key].critical_threshold,
                    time_window: config.data.result[key].critical_time_window,
                    enabled: (config.data.result[key].critical_enabled ===
                      'true'),
                  }
                  timeWindowAlerts.byId[key].warning = warning;
                  timeWindowAlerts.byId[key].critical = critical;
                  timeWindowAlerts.byId[key].enabled = (config.data.result[key]
                    .enabled === 'true');
                }else if (key in severityAlerts.byId) {
                  severityAlerts.byId[key].parent_id = config.data.result[key]
                    .parent_id;
                  severityAlerts.byId[key].severity = config.data.result[key]
                    .severity;
                  severityAlerts.byId[key].enabled = (config.data.result[key]
                    .enabled === 'true');
                }
              });
              payload = {
                chain_name: res[3],
                parent_id: parent_id,
                alerts: repeatAlerts,
              }
              loadRepeatAlertsSubstrateDetails(payload);
              payload = {
                chain_name: res[3],
                parent_id: parent_id,
                alerts: timeWindowAlerts,
              }
              loadTimeWindowAlertsSubstrateDetails(payload);
              payload = {
                chain_name: res[3],
                parent_id: parent_id,
                alerts: thresholdAlerts,
              }
              loadThresholdAlertsSubstrateDetails(payload);
              payload = {
                chain_name: res[3],
                parent_id: parent_id,
                alerts: severityAlerts,
              }
              loadSeverityAlertsSubstrateDetails(payload);
            }
          }
        }
      }
    } catch(err) {
      console.log(err);
      ToastsStore.error(
        'An Error occurred your configuration may be corrupted.', 5000);
    }
    handleClose();
  }

  render() {
    return (
      <LoadConfigButton
        onClick={this.loadConfigs}
      />
    );
  }
}

LoadConfig.propTypes = {
  loadTelegramDetails: PropTypes.func.isRequired,
  loadTwilioDetails: PropTypes.func.isRequired,
  loadEmailDetails: PropTypes.func.isRequired,
  loadPagerdutyDetails: PropTypes.func.isRequired,
  loadOpsgenieDetails: PropTypes.func.isRequired,
  loadNodeCosmosDetails: PropTypes.func.isRequired,
}

export default connect(mapStateToProps, mapDispatchToProps)(LoadConfig);
