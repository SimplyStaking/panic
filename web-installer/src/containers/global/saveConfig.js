/* eslint-disable max-len */
import React, { Component } from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { ToastsStore } from 'react-toasts';
import { SaveConfigButton } from 'utils/buttons';
import { sendConfig, deleteConfigs } from 'utils/data';
import { GENERAL } from 'constants/constants';
import { setAlertsData } from 'utils/helpers';

// List of all the data that needs to be saved in the server
const mapStateToProps = (state) => ({
  // Cosmos related data
  cosmosChains: state.CosmosChainsReducer,
  cosmosNodes: state.CosmosNodesReducer,

  // Substrate related data
  substrateChains: state.SubstrateChainsReducer,
  substrateNodes: state.SubstrateNodesReducer,

  // Chainlink related data
  chainlinkChains: state.ChainlinkChainsReducer,
  chainlinkNodes: state.ChainlinkNodesReducer,
  evmNodes: state.EvmNodesReducer,

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
  dockerHub: state.DockerHubReducer,
});

class SaveConfig extends Component {
  constructor(props) {
    super(props);
    this.saveConfigs = this.saveConfigs.bind(this);
  }

  async saveConfigs() {
    const {
      emails,
      pagerduties,
      telegrams,
      twilios,
      opsgenies,
      slacks,
      cosmosChains,
      cosmosNodes,
      chainlinkChains,
      chainlinkNodes,
      evmNodes,
      githubRepositories,
      substrateChains,
      substrateNodes,
      general,
      systems,
      dockerHub,
      closeOnSave,
    } = this.props;

    await deleteConfigs();

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

    if (slacks.allIds.length !== 0) {
      await sendConfig('channel', 'slack_config.ini', '', '', slacks.byId);
    }

    // We have to use forEach as await requires the For loop to be async
    cosmosChains.allIds.forEach(async (currentChainId) => {
      const chainConfig = cosmosChains.byId[currentChainId];
      // First we will save the nodes pertaining to the cosmos based chain
      if (chainConfig.nodes.length !== 0) {
        const nodesToSave = {};
        for (let j = 0; j < chainConfig.nodes.length; j += 1) {
          const currentId = chainConfig.nodes[j];
          nodesToSave[currentId] = cosmosNodes.byId[currentId];
        }

        // Once the node details are extracted from the list of all nodes, we
        // save it to it's own file
        await sendConfig(
          'chain',
          'nodes_config.ini',
          chainConfig.chain_name,
          'cosmos',
          nodesToSave,
        );
      }

      // Repeat the above process for githubRepositories
      if (chainConfig.githubRepositories.length !== 0) {
        const reposToSave = {};
        for (let j = 0; j < chainConfig.githubRepositories.length; j += 1) {
          const currentId = chainConfig.githubRepositories[j];
          reposToSave[currentId] = githubRepositories.byId[currentId];
        }

        // Once the node details are extracted from the list of all nodes, we
        // save it to it's own file
        await sendConfig(
          'chain',
          'github_repos_config.ini',
          chainConfig.chain_name,
          'cosmos',
          reposToSave,
        );
      }

      // Repeat the above process for dockerHub
      if (chainConfig.dockerHubs.length !== 0) {
        const dockerHubsToSave = {};
        for (let j = 0; j < chainConfig.dockerHubs.length; j += 1) {
          const currentId = chainConfig.dockerHubs[j];
          dockerHubsToSave[currentId] = dockerHub.byId[currentId];
        }

        // Once the node details are extracted from the list of all nodes, we
        // save it to it's own file
        await sendConfig(
          'chain',
          'dockerhub_repos_config.ini',
          chainConfig.chain_name,
          'cosmos',
          dockerHubsToSave,
        );
      }

      const allAlertsConfig = setAlertsData(chainConfig, currentChainId);

      await sendConfig(
        'chain',
        'alerts_config.ini',
        chainConfig.chain_name,
        'cosmos',
        allAlertsConfig,
      );
    });

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
        await sendConfig(
          'chain',
          'nodes_config.ini',
          chainConfig.chain_name,
          'substrate',
          nodesToSave,
        );
      }

      // Repeat the above process for githubRepositories
      if (chainConfig.githubRepositories.length !== 0) {
        const reposToSave = {};
        for (let j = 0; j < chainConfig.githubRepositories.length; j += 1) {
          const currentId = chainConfig.githubRepositories[j];
          reposToSave[currentId] = githubRepositories.byId[currentId];
        }

        // Once the node details are extracted from the list of all nodes, we
        // save it to it's own file
        await sendConfig(
          'chain',
          'github_repos_config.ini',
          chainConfig.chain_name,
          'substrate',
          reposToSave,
        );
      }

      // Repeat the above process for docker
      if (chainConfig.dockerHubs.length !== 0) {
        const dockerHubsToSave = {};
        for (let j = 0; j < chainConfig.dockerHubs.length; j += 1) {
          const currentId = chainConfig.dockerHubs[j];
          dockerHubsToSave[currentId] = dockerHub.byId[currentId];
        }

        // Once the node details are extracted from the list of all nodes, we
        // save it to it's own file
        await sendConfig(
          'chain',
          'dockerhub_repos_config.ini',
          chainConfig.chain_name,
          'substrate',
          dockerHubsToSave,
        );
      }

      const allAlertsConfig = setAlertsData(chainConfig, currentChainId);

      await sendConfig(
        'chain',
        'alerts_config.ini',
        chainConfig.chain_name,
        'substrate',
        allAlertsConfig,
      );
    });

    // We have to use forEach as await requires the For loop to be async
    chainlinkChains.allIds.forEach(async (currentChainId) => {
      const chainConfig = chainlinkChains.byId[currentChainId];
      const evmUrls = [];
      const { weiWatchers } = chainlinkChains.byId[currentChainId];

      await sendConfig('chain', 'weiwatchers_config.ini', chainConfig.chain_name, 'chainlink', {
        weitwatchers: weiWatchers,
      });
      if (chainConfig.evmNodes.length !== 0) {
        const evmNodesToSave = {};

        for (let k = 0; k < chainConfig.evmNodes.length; k += 1) {
          const currentId = chainConfig.evmNodes[k];
          evmNodesToSave[currentId] = evmNodes.byId[currentId];
          evmUrls.push(evmNodes.byId[currentId].node_http_url);
        }

        // Once the node details are extracted from the list of all nodes, we
        // save it to it's own file
        await sendConfig(
          'chain',
          'evm_nodes_config.ini',
          chainConfig.chain_name,
          'chainlink',
          evmNodesToSave,
        );
      }

      // First we will save the nodes pertaining to the substrate based chain
      if (chainConfig.nodes.length !== 0) {
        const nodesToSave = {};

        for (let j = 0; j < chainConfig.nodes.length; j += 1) {
          const currentId = chainConfig.nodes[j];
          nodesToSave[currentId] = chainlinkNodes.byId[currentId];
          nodesToSave[currentId].evm_nodes_urls = evmUrls;
          nodesToSave[currentId].weiwatchers_url = weiWatchers.weiwatchers_url;
          nodesToSave[currentId].monitor_contracts = weiWatchers.monitor_contracts;
        }

        // Once the node details are extracted from the list of all nodes, we
        // save it to it's own file
        await sendConfig(
          'chain',
          'nodes_config.ini',
          chainConfig.chain_name,
          'chainlink',
          nodesToSave,
        );
      }

      // Repeat the above process for githubRepositories
      if (chainConfig.githubRepositories.length !== 0) {
        const reposToSave = {};
        for (let j = 0; j < chainConfig.githubRepositories.length; j += 1) {
          const currentId = chainConfig.githubRepositories[j];
          reposToSave[currentId] = githubRepositories.byId[currentId];
        }

        // Once the node details are extracted from the list of all nodes, we
        // save it to it's own file
        await sendConfig(
          'chain',
          'github_repos_config.ini',
          chainConfig.chain_name,
          'chainlink',
          reposToSave,
        );
      }

      // Repeat the above process for dockerHub
      if (chainConfig.dockerHubs.length !== 0) {
        const dockerHubsToSave = {};
        for (let j = 0; j < chainConfig.dockerHubs.length; j += 1) {
          const currentId = chainConfig.dockerHubs[j];
          dockerHubsToSave[currentId] = dockerHub.byId[currentId];
        }

        // Once the node details are extracted from the list of all nodes, we
        // save it to it's own file
        await sendConfig(
          'chain',
          'dockerhub_repos_config.ini',
          chainConfig.chain_name,
          'chainlink',
          dockerHubsToSave,
        );
      }

      // Repeat the above process for systems
      if (chainConfig.systems.length !== 0) {
        const systemsToSave = {};
        for (let j = 0; j < chainConfig.systems.length; j += 1) {
          const currentId = chainConfig.systems[j];
          systemsToSave[currentId] = systems.byId[currentId];
        }

        // Once the node details are extracted from the list of all nodes, we
        // save it to it's own file
        await sendConfig(
          'chain',
          'systems_config.ini',
          chainConfig.chain_name,
          'chainlink',
          systemsToSave,
        );
      }

      const allAlertsConfig = setAlertsData(chainConfig, currentChainId);

      await sendConfig(
        'chain',
        'alerts_config.ini',
        chainConfig.chain_name,
        'chainlink',
        allAlertsConfig,
      );
    });

    const generalSystems = {};
    for (let k = 0; k < general.systems.length; k += 1) {
      generalSystems[general.systems[k]] = systems.byId[general.systems[k]];
    }
    await sendConfig('general', 'systems_config.ini', '', '', generalSystems);

    const generalRepos = {};
    for (let k = 0; k < general.githubRepositories.length; k += 1) {
      generalRepos[general.githubRepositories[k]] = githubRepositories.byId[general.githubRepositories[k]];
    }
    await sendConfig('general', 'github_repos_config.ini', '', '', generalRepos);

    const generalDockerHub = {};
    for (let k = 0; k < general.dockerHubs.length; k += 1) {
      generalDockerHub[general.dockerHubs[k]] = dockerHub.byId[general.dockerHubs[k]];
    }
    await sendConfig('general', 'dockerhub_repos_config.ini', '', '', generalDockerHub);

    const allAlertsConfig = setAlertsData(general, 'GENERAL');
    await sendConfig('general', 'alerts_config.ini', '', '', allAlertsConfig);

    closeOnSave();
    ToastsStore.success('Saved Configs!', 5000);
  }

  render() {
    return <SaveConfigButton onClick={this.saveConfigs} />;
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
      twilio_phone_no: PropTypes.string,
      twilio_phone_numbers_to_dial_valid: PropTypes.arrayOf(PropTypes.string),
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  slacks: PropTypes.shape({
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
  dockerHub: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      parent_id: PropTypes.string,
      name: PropTypes.string,
      monitor_docker: PropTypes.bool,
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
            timewindow: PropTypes.number,
            enabled: PropTypes.bool,
          }),
          critical: PropTypes.shape({
            threshold: PropTypes.number,
            timewindow: PropTypes.number,
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
  cosmosNodes: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      parent_id: PropTypes.string,
      name: PropTypes.string,
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
            timewindow: PropTypes.number,
            enabled: PropTypes.bool,
          }),
          critical: PropTypes.shape({
            threshold: PropTypes.number,
            timewindow: PropTypes.number,
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
  chainlinkNodes: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      parent_id: PropTypes.string,
      name: PropTypes.string,
      node_prometheus_urls: PropTypes.string,
      monitor_prometheus: PropTypes.bool,
      monitor_node: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  evmNodes: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      parent_id: PropTypes.string,
      name: PropTypes.string,
      node_http_url: PropTypes.string,
      monitor_node: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  githubRepositories: PropTypes.shape({
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
            timewindow: PropTypes.number,
            enabled: PropTypes.bool,
          }),
          critical: PropTypes.shape({
            threshold: PropTypes.number,
            timewindow: PropTypes.number,
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
  substrateNodes: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      parent_id: PropTypes.string,
      name: PropTypes.string.isRequired,
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
    githubRepositories: PropTypes.arrayOf(PropTypes.string).isRequired,
    systems: PropTypes.arrayOf(PropTypes.string).isRequired,
    dockerHubs: PropTypes.arrayOf(PropTypes.string).isRequired,
    telegrams: PropTypes.arrayOf(PropTypes.string).isRequired,
    twilios: PropTypes.arrayOf(PropTypes.string).isRequired,
    emails: PropTypes.arrayOf(PropTypes.string).isRequired,
    pagerduties: PropTypes.arrayOf(PropTypes.string).isRequired,
    opsgenies: PropTypes.arrayOf(PropTypes.string).isRequired,
    slacks: PropTypes.arrayOf(PropTypes.string).isRequired,
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
  }).isRequired,
  closeOnSave: PropTypes.func.isRequired,
};

export default connect(mapStateToProps)(SaveConfig);
