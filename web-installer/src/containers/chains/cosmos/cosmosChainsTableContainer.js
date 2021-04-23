import { connect } from 'react-redux';
import CosmosChainsTable from 'components/chains/cosmos/tables/cosmosChainsTable';
import {
  removeChainCosmos,
  loadConfigCosmos,
  removeNodeCosmos,
} from 'redux/actions/cosmosActions';
import {
  removeRepository,
  removeKms,
  removeTelegramChannel,
  removeTwilioChannel,
  removeEmailChannel,
  removePagerDutyChannel,
  removeOpsGenieChannel,
} from 'redux/actions/generalActions';
import { changePage } from 'redux/actions/pageActions';

// We will need the configured state of the cosmos nodes
const mapStateToProps = (state) => ({
  telegrams: state.TelegramsReducer,
  twilios: state.TwiliosReducer,
  emails: state.EmailsReducer,
  pagerduties: state.PagerDutyReducer,
  opsgenies: state.OpsGenieReducer,
  slacks: state.SlacksReducer,
  config: state.CosmosChainsReducer,
});

// Functions required are to change page, remove the chain details
// later to also load the chain details.
function mapDispatchToProps(dispatch) {
  return {
    pageChanger: (page) => dispatch(changePage(page)),
    removeChainDetails: (details) => dispatch(removeChainCosmos(details)),
    removeNodeDetails: (details) => dispatch(removeNodeCosmos(details)),
    removeRepositoryDetails: (details) => dispatch(removeRepository(details)),
    removeKmsDetails: (details) => dispatch(removeKms(details)),
    loadConfigDetails: (details) => dispatch(loadConfigCosmos(details)),
    removeOpsGenieDetails: (details) => dispatch(removeOpsGenieChannel(details)),
    removePagerDutyDetails: (details) => dispatch(removePagerDutyChannel(details)),
    removeEmailDetails: (details) => dispatch(removeEmailChannel(details)),
    removeTwilioDetails: (details) => dispatch(removeTwilioChannel(details)),
    removeTelegramDetails: (details) => dispatch(removeTelegramChannel(details)),
  };
}

const CosmosChainsTableContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(CosmosChainsTable);

export default CosmosChainsTableContainer;
