import { withFormik } from 'formik';
import { connect } from 'react-redux';
import PagerDutyForm from 'components/channels/forms/pagerDutyForm';
import PagerDutyTable from 'components/channels/tables/pagerDutyTable';
import { addPagerDuty, removePagerDuty } from 'redux/actions/channelActions';
import PagerDutySchema from './schemas/pagerDutySchema';

const Form = withFormik({
  mapPropsToErrors: () => ({
    channel_name: '',
    api_token: '',
    integration_key: '',
  }),
  mapPropsToValues: () => ({
    channel_name: '',
    api_token: '',
    integration_key: '',
    info: false,
    warning: false,
    critical: false,
    error: false,
  }),
  validationSchema: (props) => PagerDutySchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { savePagerDutyDetails } = props;
    const payload = {
      channel_name: values.channel_name,
      api_token: values.api_token,
      integration_key: values.integration_key,
      info: values.info,
      warning: values.warning,
      critical: values.critical,
      error: values.error,
      parent_ids: [],
      parent_names: [],
    };
    savePagerDutyDetails(payload);
    resetForm();
  },
})(PagerDutyForm);

const mapStateToProps = (state) => ({
  emails: state.EmailsReducer,
  opsGenies: state.OpsGenieReducer,
  pagerDuties: state.PagerDutyReducer,
  telegrams: state.TelegramsReducer,
  twilios: state.TwiliosReducer,
  slacks: state.SlacksReducer,
});

function mapDispatchToProps(dispatch) {
  return {
    savePagerDutyDetails: (details) => dispatch(addPagerDuty(details)),
  };
}

function mapDispatchToPropsRemove(dispatch) {
  return {
    removePagerDutyDetails: (details) => dispatch(removePagerDuty(details)),
  };
}

const PagerDutyFormContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Form);

const PagerDutyTableContainer = connect(
  mapStateToProps,
  mapDispatchToPropsRemove,
)(PagerDutyTable);

export { PagerDutyFormContainer, PagerDutyTableContainer };
