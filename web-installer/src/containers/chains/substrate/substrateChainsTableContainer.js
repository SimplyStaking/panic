import { connect } from 'react-redux';
import SubstrateChainsTable from 'components/chains/substrate/tables/substrateChainsTable';
import {
  removeChainSubstrate,
  loadConfigSubstrate,
  removeNodeSubstrate,
} from 'redux/actions/substrateActions';
import {
  removeRepository,
  removeTelegramChannel,
  removeTwilioChannel,
  removeEmailChannel,
  removePagerDutyChannel,
  removeOpsGenieChannel,
} from 'redux/actions/generalActions';
import { changePage } from 'redux/actions/pageActions';

// We will need the configured state of the substrate nodes
const mapStateToProps = (state) => ({
  telegrams: state.TelegramsReducer,
  twilios: state.TwiliosReducer,
  emails: state.EmailsReducer,
  pagerduties: state.PagerDutyReducer,
  opsgenies: state.OpsGenieReducer,
  config: state.SubstrateChainsReducer,
});

// Functions required are to change page, remove the chain details
// later to also load the chain details.
function mapDispatchToProps(dispatch) {
  return {
    pageChanger: (page) => dispatch(changePage(page)),
    removeChainDetails: (details) => dispatch(removeChainSubstrate(details)),
    removeNodeDetails: (details) => dispatch(removeNodeSubstrate(details)),
    removeRepositoryDetails: (details) => dispatch(removeRepository(details)),
    loadConfigDetails: (details) => dispatch(loadConfigSubstrate(details)),
    removeOpsGenieDetails: (details) => dispatch(removeOpsGenieChannel(details)),
    removePagerDutyDetails: (details) => dispatch(removePagerDutyChannel(details)),
    removeEmailDetails: (details) => dispatch(removeEmailChannel(details)),
    removeTwilioDetails: (details) => dispatch(removeTwilioChannel(details)),
    removeTelegramDetails: (details) => dispatch(removeTelegramChannel(details)),
  };
}

const SubstrateChainsTableContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(SubstrateChainsTable);

export default SubstrateChainsTableContainer;
