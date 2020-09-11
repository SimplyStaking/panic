import { withFormik } from 'formik';
import { connect } from 'react-redux';
import ChannelsTable from '../../../components/chains/cosmos/tables/channelsTable';
import { addChannel, removeChannel } from '../../../redux/actions/chainsActions';

const Form = withFormik({
  mapPropsToValues: () => ({
    telegrams: [],
    opsgenies: [],
    emails: [],
    pagerduties: [],
    twilios: [],
  }),
  handleSubmit: (values, { props }) => {
    const { saveChannelsDetails } = props;
    const payload = {
      telegrams: values.telegrams,
      opsgenies: values.opsgenies,
      emails: values.emails,
      pagerduties: values.pagerduties,
      twilios: values.twilios,
    };
    saveChannelsDetails(payload);
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
    saveChannelDetails: (details) => dispatch(addChannel(details)),
    removeChannelDetails: (details) => dispatch(removeChannel(details)),
  };
}

const ChannelsTableContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Form);

export default ChannelsTableContainer;
