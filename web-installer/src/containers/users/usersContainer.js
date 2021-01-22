import { withFormik } from 'formik';
import { connect } from 'react-redux';
import UsersForm from 'components/users/usersForm';
import UsersTable from 'components/users/usersTable';
import { addUser, removeUser } from 'redux/actions/usersActions';
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
  handleSubmit: ({ resetForm }) => {
    resetForm();
  },
})(UsersForm);

const mapStateToProps = (state) => ({
  users: state.UsersReducer.users,
});

function mapDispatchToProps(dispatch) {
  return {
    saveUserDetails: (details) => dispatch(addUser(details)),
  };
}

function mapDispatchToPropsRemove(dispatch) {
  return {
    removeUserDetails: (details) => dispatch(removeUser(details)),
  };
}

const UsersFormContainer = connect(mapStateToProps, mapDispatchToProps)(Form);

const UsersTableContainer = connect(
  mapStateToProps,
  mapDispatchToPropsRemove,
)(UsersTable);

export { UsersFormContainer, UsersTableContainer };
