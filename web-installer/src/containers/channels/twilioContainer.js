import { withFormik } from 'formik';
import { connect } from 'react-redux';
import TwilioForm from 'components/channels/forms/twilioForm';
import TwilioTable from 'components/channels/tables/twilioTable';
import { addTwilio, removeTwilio } from 'redux/actions/channelActions';
import TwilioSchema from './schemas/twilioSchema';

const Form = withFormik({
  mapPropsToErrors: () => ({
    configName: '',
    accountSid: '',
    authToken: '',
    twilioPhoneNo: '',
    twilioPhoneNumbersToDialValid: '',
  }),
  mapPropsToValues: () => ({
    configName: '',
    accountSid: '',
    authToken: '',
    twilioPhoneNo: '',
    twilioPhoneNumbersToDialValid: [],
  }),
  validationSchema: (props) => TwilioSchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveTwilioDetails } = props;
    const payload = {
      configName: values.configName,
      accountSid: values.accountSid,
      authToken: values.authToken,
      twilioPhoneNo: values.twilioPhoneNo,
      twilioPhoneNumbersToDialValid: values.twilioPhoneNumbersToDialValid,
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
