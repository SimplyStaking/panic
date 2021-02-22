import { withFormik } from 'formik';
import { connect } from 'react-redux';
import EmailForm from 'components/channels/forms/emailForm';
import EmailTable from 'components/channels/tables/emailTable';
import { addEmail, removeEmail } from 'redux/actions/channelActions';
import EmailSchema from './schemas/emailSchema';

const Form = withFormik({
  mapPropsToErrors: () => ({
    channel_name: '',
    smtp: '',
    port: '',
    email_from: '',
    emailTo: '',
  }),
  mapPropsToValues: () => ({
    channel_name: '',
    smtp: '',
    port: 0,
    email_from: '',
    emails_to: [],
    username: '',
    password: '',
    info: false,
    warning: false,
    critical: false,
    error: false,
  }),
  validationSchema: (props) => EmailSchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveEmailDetails } = props;
    const payload = {
      channel_name: values.channel_name,
      smtp: values.smtp,
      port: values.port,
      email_from: values.email_from,
      emails_to: values.emails_to,
      username: values.username,
      password: values.password,
      info: values.info,
      warning: values.warning,
      critical: values.critical,
      error: values.error,
    };
    saveEmailDetails(payload);
    resetForm();
  },
})(EmailForm);

const mapStateToProps = (state) => ({
  emails: state.EmailsReducer,
  opsGenies: state.OpsGenieReducer,
  pagerDuties: state.PagerDutyReducer,
  telegrams: state.TelegramsReducer,
  twilios: state.TwiliosReducer,
});

function mapDispatchToProps(dispatch) {
  return {
    saveEmailDetails: (details) => dispatch(addEmail(details)),
  };
}

function mapDispatchToPropsRemove(dispatch) {
  return {
    removeEmailDetails: (details) => dispatch(removeEmail(details)),
  };
}

const EmailFormContainer = connect(mapStateToProps, mapDispatchToProps)(Form);

const EmailTableContainer = connect(
  mapStateToProps,
  mapDispatchToPropsRemove,
)(EmailTable);

export { EmailFormContainer, EmailTableContainer };
