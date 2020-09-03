import { withFormik } from 'formik';
import { connect } from 'react-redux';
import EmailForm from '../../components/channels/forms/email_form';
import EmailTable from '../../components/channels/tables/email_table';
import { addEmail, removeEmail } from '../../redux/actions/channelActions';
import EmailSchema from './schemas/emailSchema';

const Form = withFormik({
  mapPropsToErrors: () => ({
    configName: '',
    smtp: '',
    emailFrom: '',
    emailTo: '',
    username: '',
    password: '',
  }),
  mapPropsToValues: () => ({
    configName: '',
    smtp: '',
    emailFrom: '',
    emailsTo: [],
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
      configName: values.configName,
      smtp: values.smtp,
      emailFrom: values.emailFrom,
      emailsTo: values.emailsTo,
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
  emails: state.ChannelsReducer.emails,
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

const EmailFormContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Form);

const EmailTableContainer = connect(
  mapStateToProps,
  mapDispatchToPropsRemove,
)(EmailTable);

export {
  EmailFormContainer,
  EmailTableContainer,
};
