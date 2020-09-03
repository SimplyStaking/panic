import * as Yup from 'yup';

const EmailSchema = (props) => Yup.object().shape({
  configName: Yup.string()
    .test(
      'unique-config-name',
      'Email config name is not unique.',
      (value) => {
        const { emails } = props;
        if (emails.length === 0) {
          return true;
        }
        for (let i = 0; i < emails.length; i += 1) {
          if (emails[i].configName === value) {
            return false;
          }
        }
        return true;
      },
    )
    .required('Config name is required.'),
  smtp: Yup.string()
    .required('SMTP is required.'),
  emailFrom: Yup.string()
    .email('Email is not valid.')
    .required('Email From is required.'),
  emailsTo: Yup.string()
    .test(
      'invalid-email-entered',
      'Invalid email detected, please enter a valid email.',
      (value) => {
        if (value.length === 0) {
          return true;
        }
        const emailList = value.split(',');
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        for (let i = 0; i < emailList.length; i += 1) {
          if (!emailRegex.test(emailList[i])) {
            return false;
          }
        }
        return true;
      },
    ),
  username: Yup.string()
    .required('Username  is required.'),
  password: Yup.string()
    .required('Password  is required.'),
});

export default EmailSchema;
