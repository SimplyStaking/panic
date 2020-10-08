import * as Yup from 'yup';

const UsersSchema = (props) => Yup.object().shape({
  username: Yup.string()
    .test(
      'unique-username',
      'Username is not unique.',
      (value) => {
        const { users } = props;
        if (users.length === 0) {
          return true;
        }
        for (let i = 0; i < users.length; i += 1) {
          if (users[i].username === value) {
            return false;
          }
        }
        return true;
      },
    )
    .required('Username  is required.'),
  password: Yup.string()
    .test(
      'password-length',
      'Password too short, please provide at least 8 characters',
      (value) => {
        if (value.length < 8) {
          return false;
        }
        return true;
      },
    )
    .required('Password  is required.'),
});

export default UsersSchema;
