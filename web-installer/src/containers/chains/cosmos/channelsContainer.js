import { withFormik } from 'formik';
import { connect } from 'react-redux';
import ChannelsTable from '../../../components/chains/cosmos/tables/channelsTable';
import { addTelegramChannel, removeTelegramChannel } from '../../../redux/actions/chainsActions';

const Form = withFormik({
  handleSubmit: (values, { props }) => {
    const { saveTelegramDetails } = props;
    const payload = {
      telegram: values.telegram,
    };
    saveTelegramDetails(payload);
  },
})(ChannelsTable);

const mapStateToProps = (state) => ({
  telegrams: state.ChannelsReducer.telegrams,
  twilios: state.ChannelsReducer.twilios,
  emails: state.ChannelsReducer.emails,
  pagerDuties: state.ChannelsReducer.pagerDuties,
  opsGenies: state.ChannelsReducer.opsGenies,
  config: state.ChainsReducer.config,
});

function mapDispatchToProps(dispatch) {
  return {
    saveTelegramDetails: (details) => dispatch(addTelegramChannel(details)),
    removeTelegramDetails: (details) => dispatch(removeTelegramChannel(details)),
  };
}

const ChannelsTableContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Form);

export default ChannelsTableContainer;
