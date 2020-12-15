import { withFormik } from 'formik';
import { connect } from 'react-redux';
import TwilioForm from 'components/channels/forms/twilioForm';
import TwilioTable from 'components/channels/tables/twilioTable';
import { addTwilio, removeTwilio } from 'redux/actions/channelActions';
import TwilioSchema from './schemas/twilioSchema';

const Form = withFormik({
  mapPropsToErrors: () => ({
    channel_name: '',
    account_sid: '',
    auth_token: '',
    twilio_phone_num: '',
    twilio_phone_numbers_to_dial: '',
  }),
  mapPropsToValues: () => ({
    channel_name: '',
    account_sid: '',
    auth_token: '',
    twilio_phone_num: '',
    twilio_phone_numbers_to_dial: [],
  }),
  validationSchema: (props) => TwilioSchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveTwilioDetails } = props;
    const payload = {
      channel_name: values.channel_name,
      account_sid: values.account_sid,
      auth_token: values.auth_token,
      twilio_phone_num: values.twilio_phone_num,
      twilio_phone_numbers_to_dial: values.twilio_phone_numbers_to_dial,
    };
    saveTwilioDetails(payload);
    resetForm();
  },
})(TwilioForm);

const mapStateToProps = (state) => ({
  twilios: state.TwiliosReducer,
});

function mapDispatchToProps(dispatch) {
  return {
    saveTwilioDetails: (details) => dispatch(addTwilio(details)),
  };
}

function mapDispatchToPropsRemove(dispatch) {
  return {
    removeTwilioDetails: (details) => dispatch(removeTwilio(details)),
  };
}

const TwilioFormContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Form);

const TwilioTableContainer = connect(
  mapStateToProps,
  mapDispatchToPropsRemove,
)(TwilioTable);

export {
  TwilioFormContainer,
  TwilioTableContainer,
};
