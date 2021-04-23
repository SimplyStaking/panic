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
  addSystem,
  addRepository,
} from 'redux/actions/generalActions';
import {
  addChainCosmos,
} from 'redux/actions/cosmosActions';
import {
  addChainSubstrate,
} from 'redux/actions/substrateActions';

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
  general: state.GeneralReducer.byId[GENERAL],
  systems: state.SystemsReducer,
  periodic: state.PeriodicReducer,
});

function mapDispatchToProps(dispatch) {
  return {
    addChainCosmosDetails: (details) => dispatch(addChainCosmos(details)),
    addChainSubstrateDetails: (details) => dispatch(addChainSubstrate(details)),
    addSystemDetails: (details) => dispatch(addSystem(details)),
    addRepositoryDetails: (details) => dispatch(addRepository(details)),
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
      addSystemDetails,
      addRepositoryDetails,
      addChainCosmosDetails,
      addChainSubstrateDetails,
      cosmosChains,
      substrateChains,
    } = this.props;

    ToastsStore.info('Attempting to Load Configuration.', 5000);
    const paths = await getConfigPaths();
    const files = paths.data.result;
    // let payload = {};
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
          } else if (filePath[1] === 'systems_config.ini') {
            config = await getConfig('general', 'system_config.ini', '', '');
            Object.values(config.data.result).forEach((value) => {
              const payload = JSON.parse(JSON.stringify(value));
              payload.monitor_system = payload.monitor_system === 'true';
              addSystemDetails(payload);
            });
          } else if (filePath[1] === 'alerts_config.ini') {
            config = await getConfig('general', 'alerts_config.ini', '', '');
            Object.values(config.data.result).forEach((value) => {
              const payload = JSON.parse(JSON.stringify(value));
              payload.enabled = payload.enabled === 'true';
              addSystemDetails(payload);
            });
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
            }
          }
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
    return <LoadConfigButton onClick={this.loadConfigs} />;
  }
}

LoadConfig.propTypes = {
  addSystemDetails: PropTypes.func.isRequired,
  addRepositoryDetails: PropTypes.func.isRequired,
  addChainCosmosDetails: PropTypes.func.isRequired,
  addChainSubstrateDetails: PropTypes.func.isRequired,
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
