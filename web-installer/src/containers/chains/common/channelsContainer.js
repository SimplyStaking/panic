import { connect } from 'react-redux';
import ChannelsTable from
  '../../../components/chains/common/tables/channelsTable';
import { GLOBAL } from '../../../constants/constants';
import {
  addTelegramChannel, removeTelegramChannel, addTwilioChannel,
  removeTwilioChannel, addEmailChannel, removeEmailChannel,
  addPagerDutyChannel, removePagerDutyChannel, addOpsGenieChannel,
  removeOpsGenieChannel,
} from '../../../redux/actions/generalActions';
import CosmosData from '../../../data/cosmos';
import SubstrateData from '../../../data/substrate';
import GeneralData from '../../../data/general';

// ------------------------- Common Actions -----------------------------

// Common actions perfromed by all the chains and general setups, to chose
// which alerting channel will be utilized for that particular setup.
function mapDispatchToProps(dispatch) {
  return {
    addTelegramDetails:
      (details) => dispatch(addTelegramChannel(details)),
    removeTelegramDetails:
      (details) => dispatch(removeTelegramChannel(details)),
    addTwilioDetails:
      (details) => dispatch(addTwilioChannel(details)),
    removeTwilioDetails:
      (details) => dispatch(removeTwilioChannel(details)),
    addEmailDetails:
      (details) => dispatch(addEmailChannel(details)),
    removeEmailDetails:
      (details) => dispatch(removeEmailChannel(details)),
    addPagerDutyDetails:
      (details) => dispatch(addPagerDutyChannel(details)),
    removePagerDutyDetails:
      (details) => dispatch(removePagerDutyChannel(details)),
    addOpsGenieDetails:
      (details) => dispatch(addOpsGenieChannel(details)),
    removeOpsGenieDetails:
      (details) => dispatch(removeOpsGenieChannel(details)),
  };
}

// ------------------------- Cosmos Based Chain Data --------------------

// Cosmos and channels redux data that will be used to control the channel table
const mapCosmosStateToProps = (state) => ({
  telegrams: state.TelegramsReducer,
  twilios: state.TwiliosReducer,
  emails: state.EmailsReducer,
  pagerduties: state.PagerDutyReducer,
  opsgenies: state.OpsGenieReducer,
  currentChain: state.CurrentCosmosChain,
  config: state.CosmosChainsReducer,
  data: CosmosData,
});

// Combine cosmos state and dispatch functions to the channels table
const ChannelsCosmosTableContainer = connect(
  mapCosmosStateToProps,
  mapDispatchToProps,
)(ChannelsTable);

// ------------------------- Substrate Based Chain Data --------------------

// Substrate and channels redux data that will be used to control the channel
// table
const mapSubstrateStateToProps = (state) => ({
  telegrams: state.TelegramsReducer,
  twilios: state.TwiliosReducer,
  emails: state.EmailsReducer,
  pagerduties: state.PagerDutyReducer,
  opsgenies: state.OpsGenieReducer,
  currentChain: state.CurrentSubstrateChain,
  config: state.SubstrateChainsReducer,
  data: SubstrateData,
});

// Combine substrate state and dispatch functions to the channels table
const ChannelsSubstrateTableContainer = connect(
  mapSubstrateStateToProps,
  mapDispatchToProps,
)(ChannelsTable);

// ------------------------- General Data  ----------------------------------

// General and channels redux data that will be used to control the channel
// table
const mapGeneralStateToProps = (state) => ({
  telegrams: state.TelegramsReducer,
  twilios: state.TwiliosReducer,
  emails: state.EmailsReducer,
  pagerduties: state.PagerDutyReducer,
  opsgenies: state.OpsGenieReducer,
  currentChain: GLOBAL,
  config: state.GeneralReducer,
  data: GeneralData,
});

// Combine general state and dispatch functions to the channels table
const ChannelsGeneralTableContainer = connect(
  mapGeneralStateToProps,
  mapDispatchToProps,
)(ChannelsTable);

export {
  ChannelsCosmosTableContainer, ChannelsSubstrateTableContainer,
  ChannelsGeneralTableContainer,
};
