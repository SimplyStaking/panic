import React, { Component } from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { SaveConfigButton } from '../../utils/buttons';
import { sendConfig } from '../../utils/data';

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
  general: state.GeneralReducer,
  systems: state.SystemsReducer,
});

class SaveConfig extends Component {
  constructor(props) {
    super(props);
    this.saveConfigs = this.saveConfigs.bind(this);
  }

  async saveConfigs() {
    const {
      emails, pagerduties, telegrams, twilios, opsgenies, cosmosChains, cosmosNodes,
      repositories, kmses, substrateChains, substrateNodes, general, systems,
    } = this.props;

    // Save all the channels configurations if any
    if (emails.allIds.length !== 0) {
      await sendConfig('channel', 'email_config.ini', '', '', emails.byId);
    }

    if (pagerduties.allIds.length !== 0) {
      await sendConfig('channel', 'pagerduty_config.ini', '', '', pagerduties.byId);
    }

    if (telegrams.allIds.length !== 0) {
      await sendConfig('channel', 'telegram_config.ini', '', '', telegrams.byId);
    }

    if (twilios.allIds.length !== 0) {
      await sendConfig('channel', 'twilio_config.ini', '', '', twilios.byId);
    }

    if (opsgenies.allIds.length !== 0) {
      await sendConfig('channel', 'opsgenie_config.ini', '', '', opsgenies.byId);
    }

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
          chainConfig.chainName, 'cosmos', nodesToSave);
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
          chainConfig.chainName, 'cosmos', reposToSave);
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
          chainConfig.chainName, 'cosmos', kmsToSave);
      }

      const channelConfigs = {};
      channelConfigs.telegram = chainConfig.telegrams;
      channelConfigs.email = chainConfig.emails;
      channelConfigs.twilio = chainConfig.twilios;
      channelConfigs.opsgenie = chainConfig.opsgenies;
      channelConfigs.pagerduty = chainConfig.pagerduties;

      // Save the channels
      await sendConfig('chain', 'channels_config.ini',
        chainConfig.chainName, 'cosmos', channelConfigs);

      // Redo the structure of these alerts to be able to save them in the .ini
      // file
      const repeatAlertsConfig = {};
      for (let i = 0; i < chainConfig.repeatAlerts.allIds.length; i += 1) {
        const id = chainConfig.repeatAlerts.allIds[i];
        repeatAlertsConfig[id] = {};
        repeatAlertsConfig[id].name = chainConfig.repeatAlerts.byId[id].name;
        repeatAlertsConfig[id].enabled = chainConfig.repeatAlerts
          .byId[id].enabled;
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
      // Save the repeatAlerts configs
      await sendConfig('chain', 'repeat_alerts_config.ini',
        chainConfig.chainName, 'cosmos', repeatAlertsConfig);

      // Redo the structure of these alerts to be able to save them in the .ini file
      const thresholdAlertsConfig = {};
      for (let i = 0; i < chainConfig.thresholdAlerts.allIds.length; i += 1) {
        const id = chainConfig.thresholdAlerts.allIds[i];
        thresholdAlertsConfig[id] = {};
        thresholdAlertsConfig[id].name = chainConfig.thresholdAlerts.byId[id]
          .name;
        thresholdAlertsConfig[id].enabled = chainConfig.thresholdAlerts.byId[id]
          .enabled;
        thresholdAlertsConfig[id].critical_threshold = chainConfig
          .thresholdAlerts.byId[id].critical.threshold;
        thresholdAlertsConfig[id].critical_enabled = chainConfig
          .thresholdAlerts.byId[id].critical.enabled;
        thresholdAlertsConfig[id].warning_threshold = chainConfig
          .thresholdAlerts.byId[id].warning.threshold;
        thresholdAlertsConfig[id].warning_enabled = chainConfig
          .thresholdAlerts.byId[id].warning.enabled;
      }

      await sendConfig('chain', 'threshold_alerts_config.ini',
        chainConfig.chainName, 'cosmos', thresholdAlertsConfig);

      await sendConfig('chain', 'severity_alerts_config.ini',
        chainConfig.chainName, 'cosmos', chainConfig.severityAlerts.byId);

      // Redo the structure of these alerts to be able to save them in the .ini
      // file
      const timeWindowAlertsConfig = {};
      for (let i = 0; i < chainConfig.timeWindowAlerts.allIds.length; i += 1) {
        const id = chainConfig.timeWindowAlerts.allIds[i];
        timeWindowAlertsConfig[id] = {};
        timeWindowAlertsConfig[id].name = chainConfig.timeWindowAlerts
          .byId[id].name;
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

      await sendConfig('chain', 'timewindow_alerts_config.ini',
        chainConfig.chainName, 'cosmos', timeWindowAlertsConfig);
    });

    // We have to use forEach as await requires the For loop to be async
    substrateChains.allIds.forEach(async (currentChainId) => {
      const chainConfig = substrateChains.byId[currentChainId];
      // First we will save the nodes pretaining to the substrate based chain
      if (chainConfig.nodes.length !== 0) {
        const nodesToSave = {};
        for (let j = 0; j < chainConfig.nodes.length; j += 1) {
          const currentId = chainConfig.nodes[j];
          nodesToSave[currentId] = substrateNodes.byId[currentId];
        }

        // Once the node details are extracted from the list of all nodes, we
        // save it to it's own file
        await sendConfig('chain', 'nodes_config.ini',
          chainConfig.chainName, 'substrate', nodesToSave);
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
          chainConfig.chainName, 'substrate', reposToSave);
      }

      const channelConfigs = {};
      channelConfigs.telegram = chainConfig.telegrams;
      channelConfigs.email = chainConfig.emails;
      channelConfigs.twilio = chainConfig.twilios;
      channelConfigs.opsgenie = chainConfig.opsgenies;
      channelConfigs.pagerduty = chainConfig.pagerduties;

      // Save the channels
      await sendConfig('chain', 'channels_config.ini',
        chainConfig.chainName, 'substrate', channelConfigs);

      // Redo the structure of these alerts to be able to save them in the .ini file
      const repeatAlertsConfig = {};
      for (let i = 0; i < chainConfig.repeatAlerts.allIds.length; i += 1) {
        const id = chainConfig.repeatAlerts.allIds[i];
        repeatAlertsConfig[id] = {};
        repeatAlertsConfig[id].name = chainConfig.repeatAlerts.byId[id].name;
        repeatAlertsConfig[id].enabled = chainConfig.repeatAlerts.byId[id]
          .enabled;
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
      // Save the repeatAlerts configs
      await sendConfig('chain', 'repeat_alerts_config.ini',
        chainConfig.chainName, 'substrate', repeatAlertsConfig);

      // Redo the structure of these alerts to be able to save them in the .ini
      // file
      const thresholdAlertsConfig = {};
      for (let i = 0; i < chainConfig.thresholdAlerts.allIds.length; i += 1) {
        const id = chainConfig.thresholdAlerts.allIds[i];
        thresholdAlertsConfig[id] = {};
        thresholdAlertsConfig[id].name = chainConfig.thresholdAlerts.byId[id]
          .name;
        thresholdAlertsConfig[id].enabled = chainConfig.thresholdAlerts
          .byId[id].enabled;
        thresholdAlertsConfig[id].critical_threshold = chainConfig
          .thresholdAlerts.byId[id].critical.threshold;
        thresholdAlertsConfig[id].critical_enabled = chainConfig
          .thresholdAlerts.byId[id].critical.enabled;
        thresholdAlertsConfig[id].warning_threshold = chainConfig
          .thresholdAlerts.byId[id].warning.threshold;
        thresholdAlertsConfig[id].warning_enabled = chainConfig
          .thresholdAlerts.byId[id].warning.enabled;
      }

      await sendConfig('chain', 'threshold_alerts_config.ini',
        chainConfig.chainName, 'substrate', thresholdAlertsConfig);
      await sendConfig('chain', 'severity_alerts_config.ini',
        chainConfig.chainName, 'substrate', chainConfig.severityAlerts.byId);

      // Redo the structure of these alerts to be able to save them in the .ini file
      const timeWindowAlertsConfig = {};
      for (let i = 0; i < chainConfig.timeWindowAlerts.allIds.length; i += 1) {
        const id = chainConfig.timeWindowAlerts.allIds[i];
        timeWindowAlertsConfig[id] = {};
        timeWindowAlertsConfig[id].name = chainConfig.timeWindowAlerts
          .byId[id].name;
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

      await sendConfig('chain', 'timewindow_alerts_config.ini',
        chainConfig.chainName, 'substrate', timeWindowAlertsConfig);
    });

    // Save the general configurations
    const channelConfigs = {};
    channelConfigs.telegram = general.telegrams;
    channelConfigs.email = general.emails;
    channelConfigs.twilio = general.twilios;
    channelConfigs.opsgenie = general.opsgenies;
    channelConfigs.pagerduty = general.pagerduties;

    // Save the channels
    await sendConfig('chain', 'channels_config.ini', 'general', 'general',
      channelConfigs);

    const generalSystems = {};
    for (let k = 0; k < general.systems.length; k += 1) {
      generalSystems[general.systems[k]] = systems.byId[general.systems[k]];
    }
    await sendConfig('chain', 'systems_config.ini', 'general', 'general',
      generalSystems);

    const generalRepos = {};
    for (let k = 0; k < general.repositories.length; k += 1) {
      generalRepos[general.repositories[k]] = repositories.byId[general.repositories[k]];
    }
    await sendConfig('chain', 'repos_config.ini', 'general', 'general',
      generalRepos);

    // Redo the structure of these alerts to be able to save them in the .ini
    // file
    const generalThreshold = {};
    for (let i = 0; i < general.thresholdAlerts.allIds.length; i += 1) {
      const id = general.thresholdAlerts.allIds[i];
      generalThreshold[id] = {};
      generalThreshold[id].name = general.thresholdAlerts.byId[id].name;
      generalThreshold[id].enabled = general.thresholdAlerts.byId[id].enabled;
      generalThreshold[id].critical_threshold = general.thresholdAlerts
        .byId[id].critical.threshold;
      generalThreshold[id].critical_enabled = general
        .thresholdAlerts.byId[id].critical.enabled;
      generalThreshold[id].warning_threshold = general
        .thresholdAlerts.byId[id].warning.threshold;
      generalThreshold[id].warning_enabled = general
        .thresholdAlerts.byId[id].warning.enabled;
    }

    await sendConfig('chain', 'threshold_alerts_config.ini', 'general',
      'general', generalThreshold);

    const generalPeriodic = { periodic: general.periodic };
    await sendConfig('chain', 'periodic_config.ini', 'general',
      'general', generalPeriodic);
  }

  render() {
    return (
      <SaveConfigButton
        onClick={this.saveConfigs}
        text="Finish"
      />
    );
  }
}

SaveConfig.propTypes = {
  emails: PropTypes.shape({
    byId: PropTypes.shape({
      configName: PropTypes.string,
      smtp: PropTypes.string,
      emailFrom: PropTypes.string,
      emailsTo: PropTypes.arrayOf(PropTypes.string),
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
      configName: PropTypes.string,
      apiToken: PropTypes.string,
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
      configName: PropTypes.string,
      apiToken: PropTypes.string,
      integrationKey: PropTypes.string,
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
      botName: PropTypes.string,
      botToken: PropTypes.string,
      chatID: PropTypes.string,
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
      configName: PropTypes.string,
      accountSid: PropTypes.string,
      authToken: PropTypes.string,
      twilioPhoneNo: PropTypes.string,
      twilioPhoneNumbersToDialValid: PropTypes.arrayOf(
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
      parentId: PropTypes.string,
      kmsName: PropTypes.string,
      exporterUrl: PropTypes.string,
      monitorKms: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  systems: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      parentId: PropTypes.string,
      name: PropTypes.string,
      exporterUrl: PropTypes.string,
      monitorSystem: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  cosmosNodes: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      parentId: PropTypes.string,
      cosmosNodeName: PropTypes.string,
      tendermintRpcUrl: PropTypes.string,
      cosmosRpcUrl: PropTypes.string,
      prometheusUrl: PropTypes.string,
      exporterUrl: PropTypes.string,
      isValidator: PropTypes.bool,
      monitorNode: PropTypes.bool,
      isArchiveNode: PropTypes.bool,
      useAsDataSource: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  repositories: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      parentId: PropTypes.string,
      repoName: PropTypes.string,
      monitorRepo: PropTypes.bool,
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
      parentId: PropTypes.string,
      substrateNodeName: PropTypes.string.isRequired,
      nodeWSURL: PropTypes.string,
      telemetryURL: PropTypes.string,
      prometheusUrl: PropTypes.string,
      exporterUrl: PropTypes.string,
      stashAddress: PropTypes.string,
      isValidator: PropTypes.bool,
      monitorNode: PropTypes.bool,
      isArchiveNode: PropTypes.bool,
      useAsDataSource: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  general: PropTypes.shape({
    repositories: PropTypes.arrayOf(PropTypes.string).isRequired,
    systems: PropTypes.arrayOf(PropTypes.string).isRequired,
    periodic: PropTypes.shape({
      time: PropTypes.string,
      enabled: PropTypes.bool,
    }),
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
};

export default connect(mapStateToProps)(SaveConfig);
