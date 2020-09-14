import { connect } from 'react-redux';
import ChannelsTable from '../../../components/chains/cosmos/tables/channelsTable';
import {
  addTelegramChannel, removeTelegramChannel, addTwilioChannel,
  removeTwilioChannel, addEmailChannel, removeEmailChannel, addPagerDutyChannel,
  removePagerDutyChannel, addOpsGenieChannel, removeOpsGenieChannel,
} from '../../../redux/actions/chainsActions';

const mapStateToProps = (state) => ({
  telegrams: state.ChannelsReducer.telegrams,
  twilios: state.ChannelsReducer.twilios,
  emails: state.ChannelsReducer.emails,
  pagerduties: state.ChannelsReducer.pagerDuties,
  opsgenies: state.ChannelsReducer.opsGenies,
  config: state.ChainsReducer.config,
});

function mapDispatchToProps(dispatch) {
  return {
    addTelegramDetails: (details) => dispatch(addTelegramChannel(details)),
    removeTelegramDetails: (details) => dispatch(removeTelegramChannel(details)),
    addTwilioDetails: (details) => dispatch(addTwilioChannel(details)),
    removeTwilioDetails: (details) => dispatch(removeTwilioChannel(details)),
    addEmailDetails: (details) => dispatch(addEmailChannel(details)),
    removeEmailDetails: (details) => dispatch(removeEmailChannel(details)),
    addPagerDutyDetails: (details) => dispatch(addPagerDutyChannel(details)),
    removePagerDutyDetails: (details) => dispatch(removePagerDutyChannel(details)),
    addOpsGenieDetails: (details) => dispatch(addOpsGenieChannel(details)),
    removeOpsGenieDetails: (details) => dispatch(removeOpsGenieChannel(details)),
  };
}

const ChannelsTableContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(ChannelsTable);

export default ChannelsTableContainer;
