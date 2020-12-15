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
import { loadChainCosmos } from 'redux/actions/cosmosActions';

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
      loadPagerdutyDetails, loadOpsgenieDetails,
    } = this.props;

    ToastsStore.info('Getting config paths.', 5000);
    const paths = await getConfigPaths();
    const files = paths.data.result;
    let config = {}
    let channels = []
    for (var i = 0; i < files.length; i++) {
      var res = files[i].split("/");
      console.log(res);
      if (res[1] == 'general') {
        if (res[2] == 'channels_config.ini') {
          config = await getConfig('general', 'channels_config.ini', '', '')
          console.log(config.data.result);
        }else if (res[2] == 'periodic_config.ini') {
          config = await getConfig('general', 'periodic_config.ini', '', '')
          console.log(config.data.result);
        }else if (res[2] == 'repos_config.ini') {
          config = await getConfig('general', 'repos_config.ini', '', '')
          console.log(config.data.result);
        }else if (res[2] == 'systems_config.ini') {
          config = await getConfig('general', 'systems_config.ini', '', '')
          console.log(config.data.result);
        }else if (res[2] == 'alerts_config.ini') {
          config = await getConfig('general', 'alerts_config.ini', '', '')
          console.log(config.data.result);
        }else{
          console.log("UWU whats this");
        }
      }else if (res[1] == 'channels') {
        if (res[2] == 'email_config.ini') {
          config = await getConfig('channel', 'email_config.ini', '', '')
          Object.keys(config.data.result).forEach(function(key) {
            loadEmailDetails(config.data.result[key]);
          });
        }else if (res[2] == 'opsgenie_config.ini') {
          config = await getConfig('channel', 'opsgenie_config.ini', '', '')
          Object.keys(config.data.result).forEach(function(key) {
            loadOpsgenieDetails(config.data.result[key]);
          });
        }else if (res[2] == 'pagerduty_config.ini') {
          config = await getConfig('channel', 'pagerduty_config.ini', '', '')
          Object.keys(config.data.result).forEach(function(key) {
            loadPagerdutyDetails(config.data.result[key]);
          });
        }else if (res[2] == 'telegram_config.ini') {
          config = await getConfig('channel', 'telegram_config.ini', '', '')
          Object.keys(config.data.result).forEach(function(key) {
            loadTelegramDetails(config.data.result[key]);
          });
        }else if (res[2] == 'twilio_config.ini') {
          config = await getConfig('channel', 'twilio_config.ini', '', '')
          Object.keys(config.data.result).forEach(function(key) {
            loadTwilioDetails(config.data.result[key]);
          });
        }else{
          console.log("UWU whats this");
        }
      } else if (res[1] == 'chains') {
        if (res[2] == 'cosmos'){
          if (res[4] == 'nodes_config.ini') {
            config = await getConfig('chain', 'nodes_config.ini', 'cosmos',
                                      res[3])
            console.log("RECEIVED NODES CONFIGS")
            Object.keys(config.data.result).forEach(function(key) {
              console.log(config.data.result[key]);
              loadChainCosmos()
            });
          } else if (res[4] == 'repos_config.ini') {

          } else if (res[4] == 'kms_config.ini') {

          } else if (res[4] == 'channels_config.ini') {

          } else if (res[4] == 'alerts_config.ini') {
          }
        } else if (res[2] == 'substrate') {
          
        } else {
          console.log("UWU WHATS THIS");
        }
      } else{
        console.log("UWU WHATS THIS");
      }
    }
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
}

export default connect(mapStateToProps, mapDispatchToProps)(LoadConfig);
