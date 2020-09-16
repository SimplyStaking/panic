import { withFormik } from 'formik';
import { connect } from 'react-redux';
import UsersForm from '../../components/users/usersForm';
import UsersTable from '../../components/users/usersTable';
import { addUser, removeUser } from '../../redux/actions/usersActions';
import UserSchema from './userSchema';

const Form = withFormik({
  mapPropsToErrors: () => ({
    username: '',
    password: '',
  }),
  mapPropsToValues: () => ({
    username: '',
    password: '',
  }),
  validationSchema: (props) => UserSchema(props),
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
