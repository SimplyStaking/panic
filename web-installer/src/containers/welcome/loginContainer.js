import { withFormik } from 'formik';
import { connect } from 'react-redux';
import LoginForm from '../../components/welcome/loginForm';
import { login, setAuthenticated } from '../../redux/actions/loginActions';
import { changePage } from '../../redux/actions/pageActions';
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
  page: state.ChangePageReducer.page,
});

function mapDispatchToProps(dispatch) {
  return {
    loginDetails: (details) => dispatch(login(details)),
    authenticate: (details) => dispatch(setAuthenticated(details)),
    pageChanger: (page) => dispatch(changePage(page)),
  };
}

const UsersFormContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Form);

export default UsersFormContainer;
