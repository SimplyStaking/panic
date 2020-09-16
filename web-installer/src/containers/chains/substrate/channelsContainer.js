import { connect } from 'react-redux';
import ChannelsTable from '../../../components/chains/cosmos/tables/channelsTable';
import {
  addTelegramChannelSubstrate, removeTelegramChannelSubstrate,
  addTwilioChannelSubstrate, removeTwilioChannelSubstrate,
  addEmailChannelSubstrate, removeEmailChannelSubstrate,
  addPagerDutyChannelSubstrate, removePagerDutyChannelSubstrate,
  addOpsGenieChannelSubstrate, removeOpsGenieChannelSubstrate,
} from '../../../redux/actions/substrateChainsActions';

const mapStateToProps = (state) => ({
  telegrams: state.ChannelsReducer.telegrams,
  twilios: state.ChannelsReducer.twilios,
  emails: state.ChannelsReducer.emails,
  pagerduties: state.ChannelsReducer.pagerDuties,
  opsgenies: state.ChannelsReducer.opsGenies,
  config: state.SubstrateChainsReducer.config,
});

function mapDispatchToProps(dispatch) {
  return {
    addTelegramDetails:
      (details) => dispatch(addTelegramChannelSubstrate(details)),
    removeTelegramDetails:
      (details) => dispatch(removeTelegramChannelSubstrate(details)),
    addTwilioDetails:
      (details) => dispatch(addTwilioChannelSubstrate(details)),
    removeTwilioDetails:
      (details) => dispatch(removeTwilioChannelSubstrate(details)),
    addEmailDetails:
      (details) => dispatch(addEmailChannelSubstrate(details)),
    removeEmailDetails:
      (details) => dispatch(removeEmailChannelSubstrate(details)),
    addPagerDutyDetails:
      (details) => dispatch(addPagerDutyChannelSubstrate(details)),
    removePagerDutyDetails:
      (details) => dispatch(removePagerDutyChannelSubstrate(details)),
    addOpsGenieDetails:
      (details) => dispatch(addOpsGenieChannelSubstrate(details)),
    removeOpsGenieDetails:
      (details) => dispatch(removeOpsGenieChannelSubstrate(details)),
  };
}

const ChannelsTableContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(ChannelsTable);

export default ChannelsTableContainer;
