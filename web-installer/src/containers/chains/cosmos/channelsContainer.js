import { connect } from 'react-redux';
import ChannelsTable from '../../../components/chains/cosmos/tables/channelsTable';
import {
  addTelegramChannelCosmos, removeTelegramChannelCosmos, addTwilioChannelCosmos,
  removeTwilioChannelCosmos, addEmailChannelCosmos, removeEmailChannelCosmos, addPagerDutyChannelCosmos,
  removePagerDutyChannelCosmos, addOpsGenieChannelCosmos, removeOpsGenieChannelCosmos,
} from '../../../redux/actions/cosmosChainsActions';

const mapStateToProps = (state) => ({
  telegrams: state.ChannelsReducer.telegrams,
  twilios: state.ChannelsReducer.twilios,
  emails: state.ChannelsReducer.emails,
  pagerduties: state.ChannelsReducer.pagerDuties,
  opsgenies: state.ChannelsReducer.opsGenies,
  config: state.CosmosChainsReducer.config,
});

function mapDispatchToProps(dispatch) {
  return {
    addTelegramDetails: (details) => dispatch(addTelegramChannelCosmos(details)),
    removeTelegramDetails: (details) => dispatch(removeTelegramChannelCosmos(details)),
    addTwilioDetails: (details) => dispatch(addTwilioChannelCosmos(details)),
    removeTwilioDetails: (details) => dispatch(removeTwilioChannelCosmos(details)),
    addEmailDetails: (details) => dispatch(addEmailChannelCosmos(details)),
    removeEmailDetails: (details) => dispatch(removeEmailChannelCosmos(details)),
    addPagerDutyDetails: (details) => dispatch(addPagerDutyChannelCosmos(details)),
    removePagerDutyDetails: (details) => dispatch(removePagerDutyChannelCosmos(details)),
    addOpsGenieDetails: (details) => dispatch(addOpsGenieChannelCosmos(details)),
    removeOpsGenieDetails: (details) => dispatch(removeOpsGenieChannelCosmos(details)),
  };
}

const ChannelsTableContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(ChannelsTable);

export default ChannelsTableContainer;
