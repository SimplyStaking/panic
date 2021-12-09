import { withFormik } from 'formik';
import { connect } from 'react-redux';
import TwilioForm from 'components/channels/forms/twilioForm';
import TwilioTable from 'components/channels/tables/twilioTable';
import { addTwilio, removeTwilio } from 'redux/actions/channelActions';
import { toggleDirty } from 'redux/actions/pageActions';
import TwilioSchema from './schemas/twilioSchema';

const Form = withFormik({
  mapPropsToErrors: () => ({
    channel_name: '',
    account_sid: '',
    auth_token: '',
    twilio_phone_no: '',
    twilio_phone_numbers_to_dial_valid: '',
  }),
  mapPropsToValues: () => ({
    channel_name: '',
    account_sid: '',
    auth_token: '',
    twilio_phone_no: '',
    twilio_phone_numbers_to_dial_valid: [],
  }),
  toggleDirtyForm: (tog, { props }) => {
    const { toggleDirtyForm } = props;
    toggleDirtyForm(tog);
  },
  validationSchema: (props) => TwilioSchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveTwilioDetails } = props;
    const payload = {
      channel_name: values.channel_name,
      account_sid: values.account_sid,
      auth_token: values.auth_token,
      twilio_phone_no: values.twilio_phone_no,
      twilio_phone_numbers_to_dial_valid: values.twilio_phone_numbers_to_dial_valid,
      parent_ids: [],
      parent_names: [],
    };
    saveTwilioDetails(payload);
    resetForm();
  },
})(TwilioForm);

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
    saveTwilioDetails: (details) => dispatch(addTwilio(details)),
    toggleDirtyForm: (tog) => dispatch(toggleDirty(tog)),
  };
}

function mapDispatchToPropsRemove(dispatch) {
  return {
    removeTwilioDetails: (details) => dispatch(removeTwilio(details)),
  };
}

const TwilioFormContainer = connect(mapStateToProps, mapDispatchToProps)(Form);

const TwilioTableContainer = connect(
  mapStateToProps,
  mapDispatchToPropsRemove,
)(TwilioTable);

export { TwilioFormContainer, TwilioTableContainer };
