import React, { Component } from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { ToastsStore } from 'react-toasts';
import { SaveConfigButton } from 'utils/buttons';
import { sendConfig, deleteConfigs } from 'utils/data';
import { GLOBAL } from 'constants/constants';

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

class SaveConfig extends Component {
  constructor(props) {
    super(props);
    this.saveConfigs = this.saveConfigs.bind(this);
  }

  async saveConfigs() {
    const {
      emails, pagerduties, telegrams, twilios, opsgenies, cosmosChains,
      cosmosNodes, repositories, kmses, substrateChains, substrateNodes,
      general, systems, periodic,
    } = this.props;

    await deleteConfigs();

    ToastsStore.info('Starting to save data config.', 5000);
    // Save all the channels configurations if any
    if (emails.allIds.length !== 0) {
      await sendConfig('channel', 'email_config.ini', '', '', emails.byId);
    }

    if (pagerduties.allIds.length !== 0) {
      await sendConfig('channel', 'pagerduty_config.ini', '', '',
        pagerduties.byId);
    }

    if (telegrams.allIds.length !== 0) {
      await sendConfig('channel', 'telegram_config.ini', '', '',
        telegrams.byId);
    }

    if (twilios.allIds.length !== 0) {
      await sendConfig('channel', 'twilio_config.ini', '', '',
        twilios.byId);
    }

    if (opsgenies.allIds.length !== 0) {
      await sendConfig('channel', 'opsgenie_config.ini', '', '',
        opsgenies.byId);
    }
    ToastsStore.success('Saved Channel Configs!', 5000);

    // We have to use forEach as await requires the For loop to be async
    cosmosChains.allIds.forEach(async (currentChainId) => {
      const chainConfig = cosmosChains.byId[currentChainId];
      // First we will save the nodes pretaining to the cosmos based chain
      if (chainConfig.nodes.length !== 0) {
        const nodesToSave = {};
        for (let j = 0; j < chainConfig.nodes.length; j += 1) {
          const currentId = chainConfig.nodes[j];
          nodesToSave[currentId] = cosmosNodes.byId[currentId];
        }

        // Once the node details are extracted from the list of all nodes, we
        // save it to it's own file
        await sendConfig('chain', 'nodes_config.ini',
          chainConfig.chain_name, 'cosmos', nodesToSave);
      }

      // Repeat the above process for repositories
      if (chainConfig.repositories.length !== 0) {
        const reposToSave = {};
        for (let j = 0; j < chainConfig.repositories.length; j += 1) {
          const currentId = chainConfig.repositories[j];
          reposToSave[currentId] = repositories.byId[currentId];
        }

        // Once the node details are extracted from the list of all nodes, we
        // save it to it's own file
        await sendConfig('chain', 'repos_config.ini',
          chainConfig.chain_name, 'cosmos', reposToSave);
      }

      // Repeat the above process for kms configs
      if (chainConfig.kmses.length !== 0) {
        const kmsToSave = {};
        for (let j = 0; j < chainConfig.kmses.length; j += 1) {
          const currentId = chainConfig.kmses[j];
          kmsToSave[currentId] = kmses.byId[currentId];
        }

        // Once the node details are extracted from the list of all nodes, we
        // save it to it's own file
        await sendConfig('chain', 'kms_config.ini',
          chainConfig.chain_name, 'cosmos', kmsToSave);
      }

      // Redo the structure of these alerts to be able to save them in the .ini
      // file
      const repeatAlertsConfig = {};
      for (let i = 0; i < chainConfig.repeatAlerts.allIds.length; i += 1) {
        const id = chainConfig.repeatAlerts.allIds[i];
        repeatAlertsConfig[id] = {};
        repeatAlertsConfig[id].name = chainConfig.repeatAlerts.byId[id]
          .identifier;
        repeatAlertsConfig[id].parent_id = currentChainId;
        repeatAlertsConfig[id].enabled = chainConfig.repeatAlerts
          .byId[id].enabled;
        repeatAlertsConfig[id].critical_enabled = chainConfig.repeatAlerts
          .byId[id].critical.enabled;
        repeatAlertsConfig[id].critical_repeat = chainConfig.repeatAlerts
          .byId[id].critical.repeat;
        repeatAlertsConfig[id].warning_enabled = chainConfig.repeatAlerts
          .byId[id].warning.enabled;
        repeatAlertsConfig[id].warning_repeat = chainConfig.repeatAlerts
          .byId[id].warning.repeat;
      }

      // Redo the structure of these alerts to be able to save them in the .ini
      // file
      const thresholdAlertsConfig = {};
      for (let i = 0; i < chainConfig.thresholdAlerts.allIds.length; i += 1) {
        const id = chainConfig.thresholdAlerts.allIds[i];
        thresholdAlertsConfig[id] = {};
        thresholdAlertsConfig[id].name = chainConfig.thresholdAlerts.byId[id]
          .identifier;
        thresholdAlertsConfig[id].parent_id = currentChainId;
        thresholdAlertsConfig[id].enabled = chainConfig.thresholdAlerts.byId[id]
          .enabled;
        thresholdAlertsConfig[id].warning_threshold = chainConfig
          .thresholdAlerts.byId[id].warning.threshold;
        thresholdAlertsConfig[id].warning_enabled = chainConfig
          .thresholdAlerts.byId[id].warning.enabled;
        thresholdAlertsConfig[id].critical_threshold = chainConfig
          .thresholdAlerts.byId[id].critical.threshold;
        thresholdAlertsConfig[id].critical_repeat = chainConfig
          .thresholdAlerts.byId[id].critical.repeat
        thresholdAlertsConfig[id].critical_enabled = chainConfig
          .thresholdAlerts.byId[id].critical.enabled;
      }

      // Redo the structure of these alerts to be able to save them in the .ini
      // file
      const timeWindowAlertsConfig = {};
      for (let i = 0; i < chainConfig.timeWindowAlerts.allIds.length; i += 1) {
        const id = chainConfig.timeWindowAlerts.allIds[i];
        timeWindowAlertsConfig[id] = {};
        timeWindowAlertsConfig[id].name = chainConfig.timeWindowAlerts
          .byId[id].identifier;
        timeWindowAlertsConfig[id].parent_id = currentChainId;
        timeWindowAlertsConfig[id].enabled = chainConfig.timeWindowAlerts
          .byId[id].enabled;
        timeWindowAlertsConfig[id].warning_threshold = chainConfig
          .timeWindowAlerts.byId[id].warning.threshold;
        timeWindowAlertsConfig[id].warning_time_window = chainConfig
          .timeWindowAlerts.byId[id].warning.time_window;
        timeWindowAlertsConfig[id].warning_enabled = chainConfig
          .timeWindowAlerts.byId[id].warning.enabled;
        timeWindowAlertsConfig[id].critical_threshold = chainConfig
          .timeWindowAlerts.byId[id].critical.threshold;
        timeWindowAlertsConfig[id].critical_time_window = chainConfig
          .timeWindowAlerts.byId[id].critical.time_window;
        timeWindowAlertsConfig[id].critical_enabled = chainConfig
          .timeWindowAlerts.byId[id].critical.enabled;
      }

      // Redo the structure of these alerts to be able to save them in the .ini
      // file
      const severityAlertsConfig = {};
      for (let i = 0; i < chainConfig.severityAlerts.allIds.length; i += 1) {
        const id = chainConfig.severityAlerts.allIds[i];
        severityAlertsConfig[id] = {};
        severityAlertsConfig[id].name = chainConfig.severityAlerts.byId[id]
          .identifier;
        severityAlertsConfig[id].parent_id = currentChainId;
        severityAlertsConfig[id].enabled = chainConfig.severityAlerts
          .byId[id].enabled;
        severityAlertsConfig[id].severity = chainConfig.severityAlerts
          .byId[id].severity;
      }

      const allAlertsConfig = {
        ...repeatAlertsConfig, ...thresholdAlertsConfig,
        ...timeWindowAlertsConfig, ...severityAlertsConfig,
      }

      await sendConfig('chain', 'alerts_config.ini',
        chainConfig.chain_name, 'cosmos', allAlertsConfig);
    });

    ToastsStore.success('Saved Cosmos Configs!', 5000);

    // We have to use forEach as await requires the For loop to be async
    substrateChains.allIds.forEach(async (currentChainId) => {
      const chainConfig = substrateChains.byId[currentChainId];
      // First we will save the nodes pertaining to the substrate based chain
      if (chainConfig.nodes.length !== 0) {
        const nodesToSave = {};
        for (let j = 0; j < chainConfig.nodes.length; j += 1) {
          const currentId = chainConfig.nodes[j];
          nodesToSave[currentId] = substrateNodes.byId[currentId];
        }

        // Once the node details are extracted from the list of all nodes, we
        // save it to it's own file
        await sendConfig('chain', 'nodes_config.ini',
          chainConfig.chain_name, 'substrate', nodesToSave);
      }

      // Repeat the above process for repositories
      if (chainConfig.repositories.length !== 0) {
        const reposToSave = {};
        for (let j = 0; j < chainConfig.repositories.length; j += 1) {
          const currentId = chainConfig.repositories[j];
          reposToSave[currentId] = repositories.byId[currentId];
        }

        // Once the node details are extracted from the list of all nodes, we
        // save it to it's own file
        await sendConfig('chain', 'repos_config.ini',
          chainConfig.chain_name, 'substrate', reposToSave);
      }

      // Redo the structure of these alerts to be able to save them in the .ini
      // file
      const repeatAlertsConfig = {};
      for (let i = 0; i < chainConfig.repeatAlerts.allIds.length; i += 1) {
        const id = chainConfig.repeatAlerts.allIds[i];
        repeatAlertsConfig[id] = {};
        repeatAlertsConfig[id].name = chainConfig.repeatAlerts.byId[id].name;
        repeatAlertsConfig[id].enabled = chainConfig.repeatAlerts.byId[id]
          .enabled;
        repeatAlertsConfig[id].parent_id = currentChainId;
        repeatAlertsConfig[id].critical_delayed = chainConfig.repeatAlerts
          .byId[id].critical.delayed;
        repeatAlertsConfig[id].critical_enabled = chainConfig.repeatAlerts
          .byId[id].critical.enabled;
        repeatAlertsConfig[id].critical_repeat = chainConfig.repeatAlerts
          .byId[id].critical.repeat;
        repeatAlertsConfig[id].warning_delayed = chainConfig.repeatAlerts
          .byId[id].warning.delayed;
        repeatAlertsConfig[id].warning_enabled = chainConfig.repeatAlerts
          .byId[id].warning.enabled;
        repeatAlertsConfig[id].warning_repeat = chainConfig.repeatAlerts
          .byId[id].warning.repeat;
      }

      // Redo the structure of these alerts to be able to save them in the .ini
      // file
      const thresholdAlertsConfig = {};
      for (let i = 0; i < chainConfig.thresholdAlerts.allIds.length; i += 1) {
        const id = chainConfig.thresholdAlerts.allIds[i];
        thresholdAlertsConfig[id] = {};
        thresholdAlertsConfig[id].name = chainConfig.thresholdAlerts.byId[id]
          .name;
        thresholdAlertsConfig[id].parent_id = currentChainId;
        thresholdAlertsConfig[id].enabled = chainConfig.thresholdAlerts
          .byId[id].enabled;
        thresholdAlertsConfig[id].critical_threshold = chainConfig
          .thresholdAlerts.byId[id].critical.threshold;
        thresholdAlertsConfig[id].critical_repeat = chainConfig
          .thresholdAlerts.byId[id].critical.repeat;
        thresholdAlertsConfig[id].critical_enabled = chainConfig
          .thresholdAlerts.byId[id].critical.enabled;
        thresholdAlertsConfig[id].warning_threshold = chainConfig
          .thresholdAlerts.byId[id].warning.threshold;
        thresholdAlertsConfig[id].warning_enabled = chainConfig
          .thresholdAlerts.byId[id].warning.enabled;
      }

      // Redo the structure of these alerts to be able to save them in the .ini
      // file
      const timeWindowAlertsConfig = {};
      for (let i = 0; i < chainConfig.timeWindowAlerts.allIds.length; i += 1) {
        const id = chainConfig.timeWindowAlerts.allIds[i];
        timeWindowAlertsConfig[id] = {};
        timeWindowAlertsConfig[id].name = chainConfig.timeWindowAlerts
          .byId[id].name;
        timeWindowAlertsConfig[id].parent_id = currentChainId;
        timeWindowAlertsConfig[id].enabled = chainConfig.timeWindowAlerts
          .byId[id].enabled;
        timeWindowAlertsConfig[id].critical_threshold = chainConfig
          .timeWindowAlerts.byId[id].critical.threshold;
        timeWindowAlertsConfig[id].critical_timewindow = chainConfig
          .timeWindowAlerts.byId[id].critical.timewindow;
        timeWindowAlertsConfig[id].critical_enabled = chainConfig
          .timeWindowAlerts.byId[id].critical.enabled;
        timeWindowAlertsConfig[id].warning_threshold = chainConfig
          .timeWindowAlerts.byId[id].warning.threshold;
        timeWindowAlertsConfig[id].warning_timewindow = chainConfig
          .timeWindowAlerts.byId[id].warning.timewindow;
        timeWindowAlertsConfig[id].warning_enabled = chainConfig
          .timeWindowAlerts.byId[id].warning.enabled;
      }

      // Redo the structure of these alerts to be able to save them in the .ini
      // file
      const severityAlertsConfig = {};
      for (let i = 0; i < chainConfig.severityAlerts.allIds.length; i += 1) {
        const id = chainConfig.severityAlerts.allIds[i];
        severityAlertsConfig[id] = {};
        severityAlertsConfig[id].name = chainConfig.severityAlerts.byId[id]
          .identifier;
        severityAlertsConfig[id].parent_id = currentChainId;
        severityAlertsConfig[id].enabled = chainConfig.severityAlerts
          .byId[id].enabled;
        severityAlertsConfig[id].severity = chainConfig.severityAlerts
          .byId[id].severity;
      }

      const allAlertsConfig = {
        ...repeatAlertsConfig, ...thresholdAlertsConfig,
        ...timeWindowAlertsConfig, ...severityAlertsConfig,
      }

      await sendConfig('chain', 'alerts_config.ini',
        chainConfig.chain_name, 'substrate', allAlertsConfig);
    });

    ToastsStore.success('Saved Substrate Configs!', 5000);

    const generalSystems = {};
    for (let k = 0; k < general.systems.length; k += 1) {
      generalSystems[general.systems[k]] = systems.byId[general.systems[k]];
    }
    await sendConfig('general', 'systems_config.ini', '', '', generalSystems);

    const generalRepos = {};
    for (let k = 0; k < general.repositories.length; k += 1) {
      generalRepos[general.repositories[k]] =
        repositories.byId[general.repositories[k]];
    }

    await sendConfig('general', 'repos_config.ini', '', '', generalRepos);

    // Redo the structure of these alerts to be able to save them in the .ini
    // file
    const thresholdAlertsConfig = {};
    for (let i = 0; i < general.thresholdAlerts.allIds.length; i += 1) {
      const id = general.thresholdAlerts.allIds[i];
      thresholdAlertsConfig[id] = {};
      thresholdAlertsConfig[id].name = general.thresholdAlerts.byId[id].name;
      thresholdAlertsConfig[id].enabled = general.thresholdAlerts.byId[id].enabled;
      thresholdAlertsConfig[id].parent_id = 'GLOBAL';
      thresholdAlertsConfig[id].critical_threshold = general.thresholdAlerts
        .byId[id].critical.threshold;
      thresholdAlertsConfig[id].critical_repeat = general.thresholdAlerts
        .byId[id].critical.repeat;
      thresholdAlertsConfig[id].critical_enabled = general
        .thresholdAlerts.byId[id].critical.enabled;
      thresholdAlertsConfig[id].warning_threshold = general
        .thresholdAlerts.byId[id].warning.threshold;
      thresholdAlertsConfig[id].warning_enabled = general
        .thresholdAlerts.byId[id].warning.enabled;
    }

    // Redo the structure of these alerts to be able to save them in the .ini
    // file
    const repeatAlertsConfig = {};
    for (let i = 0; i < general.repeatAlerts.allIds.length; i += 1) {
      const id = general.repeatAlerts.allIds[i];
      repeatAlertsConfig[id] = {};
      repeatAlertsConfig[id].name = general.repeatAlerts.byId[id].name;
      repeatAlertsConfig[id].enabled = general.repeatAlerts.byId[id]
        .enabled;
      repeatAlertsConfig[id].parent_id = 'GLOBAL';
      repeatAlertsConfig[id].critical_delayed = general.repeatAlerts
        .byId[id].critical.delayed;
      repeatAlertsConfig[id].critical_enabled = general.repeatAlerts
        .byId[id].critical.enabled;
      repeatAlertsConfig[id].critical_repeat = general.repeatAlerts
        .byId[id].critical.repeat;
      repeatAlertsConfig[id].warning_delayed = general.repeatAlerts
        .byId[id].warning.delayed;
      repeatAlertsConfig[id].warning_enabled = general.repeatAlerts
        .byId[id].warning.enabled;
      repeatAlertsConfig[id].warning_repeat = general.repeatAlerts
        .byId[id].warning.repeat;
    }

    const allAlertsConfig = {
      ...repeatAlertsConfig, ...thresholdAlertsConfig,
    }

    await sendConfig('general', 'alerts_config.ini', '', '', allAlertsConfig);

    await sendConfig('general', 'periodic_config.ini', '', '', { periodic });

    ToastsStore.success('Saved General configs!', 5000);
  }

  render() {
    return (
      <SaveConfigButton
        onClick={this.saveConfigs}
      />
    );
  }
}

SaveConfig.propTypes = {
  emails: PropTypes.shape({
    byId: PropTypes.shape({
      channel_name: PropTypes.string,
      smtp: PropTypes.string,
      email_from: PropTypes.string,
      emails_to: PropTypes.arrayOf(PropTypes.string),
      username: PropTypes.string,
      password: PropTypes.string,
      info: PropTypes.bool,
      warning: PropTypes.bool,
      critical: PropTypes.bool,
      error: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  opsgenies: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      channel_name: PropTypes.string,
      api_token: PropTypes.string,
      info: PropTypes.bool,
      warning: PropTypes.bool,
      critical: PropTypes.bool,
      error: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  pagerduties: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      channel_name: PropTypes.string,
      api_token: PropTypes.string,
      integration_key: PropTypes.string,
      info: PropTypes.bool,
      warning: PropTypes.bool,
      critical: PropTypes.bool,
      error: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  telegrams: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      channel_name: PropTypes.string,
      bot_token: PropTypes.string,
      chat_id: PropTypes.string,
      info: PropTypes.bool,
      warning: PropTypes.bool,
      critical: PropTypes.bool,
      error: PropTypes.bool,
      alerts: PropTypes.bool,
      commands: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  twilios: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      channel_name: PropTypes.string,
      account_sid: PropTypes.string,
      auth_token: PropTypes.string,
      twilio_phone_num: PropTypes.string,
      twilio_phone_numbers_to_dial: PropTypes.arrayOf(
        PropTypes.string,
      ),
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
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
  kmses: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      parent_id: PropTypes.string,
      kms_name: PropTypes.string,
      exporter_url: PropTypes.string,
      monitor_kms: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  systems: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      parent_id: PropTypes.string,
      name: PropTypes.string,
      exporter_url: PropTypes.string,
      monitor_system: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  cosmosNodes: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      parent_id: PropTypes.string,
      cosmos_node_name: PropTypes.string,
      tendermint_rpc_url: PropTypes.string,
      cosmos_rpc_url: PropTypes.string,
      prometheus_url: PropTypes.string,
      exporter_url: PropTypes.string,
      is_validator: PropTypes.bool,
      monitor_node: PropTypes.bool,
      is_archive_node: PropTypes.bool,
      use_as_data_source: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  repositories: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      parent_id: PropTypes.string,
      repo_name: PropTypes.string,
      monitor_repo: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
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
  substrateNodes: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      parent_id: PropTypes.string,
      substrate_node_name: PropTypes.string.isRequired,
      node_ws_url: PropTypes.string,
      telemetry_url: PropTypes.string,
      prometheus_url: PropTypes.string,
      exporter_url: PropTypes.string,
      stash_address: PropTypes.string,
      is_validator: PropTypes.bool,
      monitor_node: PropTypes.bool,
      is_archive_node: PropTypes.bool,
      use_as_data_source: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  general: PropTypes.shape({
    repositories: PropTypes.arrayOf(PropTypes.string).isRequired,
    systems: PropTypes.arrayOf(PropTypes.string).isRequired,
    telegrams: PropTypes.arrayOf(PropTypes.string).isRequired,
    twilios: PropTypes.arrayOf(PropTypes.string).isRequired,
    emails: PropTypes.arrayOf(PropTypes.string).isRequired,
    pagerduties: PropTypes.arrayOf(PropTypes.string).isRequired,
    opsgenies: PropTypes.arrayOf(PropTypes.string).isRequired,
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
  }).isRequired,
  periodic: PropTypes.shape({
    time: PropTypes.string,
    enabled: PropTypes.bool,
  }).isRequired,
};

export default connect(mapStateToProps)(SaveConfig);
