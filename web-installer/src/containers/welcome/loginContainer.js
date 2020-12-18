import { withFormik } from 'formik';
import { ToastsStore } from 'react-toasts';
import { connect } from 'react-redux';
import LoginForm from 'components/welcome/loginForm';
import { login, setAuthenticated } from 'redux/actions/loginActions';
import { changePage } from 'redux/actions/pageActions';
import { getConfigPaths } from 'utils/data';
import { loadAccounts } from 'utils/data';
import { addUser } from 'redux/actions/usersActions';
import LoginSchema from './loginSchema';

async function CheckForConfigs() {
  const paths = await getConfigPaths();
  const files = paths.data.result;
  for (var i = 0; i < files.length; i++) {
    var res = files[i].split("/");
    // We are only going to check res[2] for file names, if at least one
    // valid file exists attempt to load it's config
    if (res.length >= 3){
      if (res[2] == 'periodic_config.ini' || res[2] == 'repos_config.ini'
        || res[2] == 'systems_config.ini' || res[2] == 'alerts_config.ini'
        || res[2] == 'email_config.ini' || res[2] == 'opsgenie_config.ini'
        || res[2] == 'pagerduty_config.ini' || res[2] == 'telegram_config.ini'
        || res[2] == 'twilio_config.ini'){
        return true;
      }
    }
    if (res.length >= 5){
      if (res[4] == 'nodes_config.ini' || res[4] == 'repos_config.ini'
        || res[4] == 'kms_config.ini' || res[4] == 'alerts_config.ini'){
        return true;
      }
    }
  }
  return false;
}

async function LoadUsersFromMongo(addUserRedux) {
  const accounts = await loadAccounts();
  try {
    Object.keys(accounts.data.result).forEach((key, index) => {
      addUserRedux(accounts.data.result[key].username);
    });
  }catch (err) {
    console.log(err);
    ToastsStore.info('An error has occurred when retrieving accounts from '
                   + 'mongo.', 5000);
  }
}

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
    addUserRedux: (details) => dispatch(addUser(details)),
    checkForConfigs: CheckForConfigs,
    loadUsersFromMongo: LoadUsersFromMongo,
  };
}

const UsersFormContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Form);

export default UsersFormContainer;
