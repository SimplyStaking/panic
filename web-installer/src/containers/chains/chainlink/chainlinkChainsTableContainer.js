import { connect } from 'react-redux';
import ChainlinkChainsTable from 'components/chains/chainlink/tables/chainlinkChainsTable';
import {
  removeChainChainlink,
  loadConfigChainlink,
  removeNodeChainlink,
} from 'redux/actions/chainlinkActions';
import {
  removeRepository,
  removeKms,
  removeTelegramChannel,
  removeTwilioChannel,
  removeEmailChannel,
  removePagerDutyChannel,
  removeOpsGenieChannel,
  removeSlackChannel,
} from 'redux/actions/generalActions';
import { changePage } from 'redux/actions/pageActions';

// We will need the configured state of the chainlink nodes
const mapStateToProps = (state) => ({
  telegrams: state.TelegramsReducer,
  twilios: state.TwiliosReducer,
  emails: state.EmailsReducer,
  pagerduties: state.PagerDutyReducer,
  opsgenies: state.OpsGenieReducer,
  slacks: state.SlacksReducer,
  config: state.ChainlinkChainsReducer,
});

// Functions required are to change page, remove the chain details
// later to also load the chain details.
function mapDispatchToProps(dispatch) {
  return {
    pageChanger: (page) => dispatch(changePage(page)),
    removeChainDetails: (details) => dispatch(removeChainChainlink(details)),
    removeNodeDetails: (details) => dispatch(removeNodeChainlink(details)),
    removeRepositoryDetails: (details) => dispatch(removeRepository(details)),
    removeKmsDetails: (details) => dispatch(removeKms(details)),
    loadConfigDetails: (details) => dispatch(loadConfigChainlink(details)),
    removeOpsGenieDetails: (details) => dispatch(removeOpsGenieChannel(details)),
    removePagerDutyDetails: (details) => dispatch(removePagerDutyChannel(details)),
    removeEmailDetails: (details) => dispatch(removeEmailChannel(details)),
    removeTwilioDetails: (details) => dispatch(removeTwilioChannel(details)),
    removeTelegramDetails: (details) => dispatch(removeTelegramChannel(details)),
    removeSlackDetails: (details) => dispatch(removeSlackChannel(details)),
  };
}

const ChainlinkChainsTableContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(ChainlinkChainsTable);

export default ChainlinkChainsTableContainer;
