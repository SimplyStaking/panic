import { withFormik } from 'formik';
import { connect } from 'react-redux';
import LoginForm from '../../components/welcome/loginForm';
import { login } from '../../redux/actions/loginActions';
import LoginSchema from './loginSchema';

const Form = withFormik({
  mapPropsToErrors: () => ({
    username: '',
    password: '',
  }),
  mapPropsToValues: () => ({
    username: '',
    password: '',
  }),
  validationSchema: (props) => LoginSchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { loginDetails } = props;
    const payload = {
      username: values.username,
      password: values.password,
    };
    loginDetails(payload);
    resetForm();
  },
})(LoginForm);

const mapStateToProps = (state) => ({
  users: state.UsersReducer.users,
});

function mapDispatchToProps(dispatch) {
  return {
    loginDetails: (details) => dispatch(login(details)),
  };
}

const UsersFormContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Form);

export default UsersFormContainer;
