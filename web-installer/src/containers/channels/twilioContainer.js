import { withFormik } from 'formik';
import { connect } from 'react-redux';
import TwilioForm from 'components/channels/forms/twilioForm';
import TwilioTable from 'components/channels/tables/twilioTable';
import { addTwilio, removeTwilio } from 'redux/actions/channelActions';
import TwilioSchema from './schemas/twilioSchema';

const Form = withFormik({
  mapPropsToErrors: () => ({
    config_name: '',
    account_sid: '',
    authToken: '',
    twilioPhoneNum: '',
    twilioPhoneNumbersToDial: '',
  }),
  mapPropsToValues: () => ({
    config_name: '',
    account_sid: '',
    authToken: '',
    twilioPhoneNum: '',
    twilioPhoneNumbersToDial: [],
  }),
  validationSchema: (props) => TwilioSchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveTwilioDetails } = props;
    const payload = {
      config_name: values.config_name,
      account_sid: values.account_sid,
      authToken: values.authToken,
      twilioPhoneNum: values.twilioPhoneNum,
      twilioPhoneNumbersToDial: values.twilioPhoneNumbersToDial,
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
