/* eslint-disable func-names */
import * as Yup from 'yup';
import { checkChannelName } from 'utils/helpers';

const EmailSchema = (props) => Yup.object().shape({
  channel_name: Yup.string()
    .test('unique-config-name', 'Email config name is not unique.', (value) => {
      const {
        emails, opsGenies, pagerDuties, telegrams, twilios, slacks,
      } = props;

      return checkChannelName(
        value,
        ...[emails, opsGenies, pagerDuties, telegrams, twilios, slacks],
      );
    })
    .required('Config name is required.'),
  smtp: Yup.string().required('SMTP is required.'),
  port: Yup.string().required('Port is required.'),
  email_from: Yup.string().email('Email is not valid.').required('Email From is required.'),
  emails_to: Yup.array()
    .transform(function (value, originalValue) {
      if (this.isType(value) && value !== null) {
        return value;
      }
      return originalValue ? originalValue.split(/[\s,]+/) : [];
    })
    .of(Yup.string().email(({ value }) => `${value} is not a valid email `))
    .required('Emails To is required.'),
});

export default EmailSchema;
