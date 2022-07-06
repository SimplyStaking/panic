import * as Yup from 'yup';
import { checkChannelName, checkIfDoesNotContainsSquareBracket } from 'utils/helpers';

const TwilioSchema = (props) => Yup.object().shape({
  channel_name: Yup.string()
    .test('unique-config-name', 'Twilio config name is not unique.', (value) => {
      const {
        emails, opsGenies, pagerDuties, telegrams, twilios, slacks,
      } = props;
      return checkChannelName(
        value,
        ...[emails, opsGenies, pagerDuties, telegrams, twilios, slacks],
      );
    })
    .test('does-not-contain-square-bracket', 'Twilio config name contains a square bracket',
      (value) => checkIfDoesNotContainsSquareBracket(value))
    .required('Config name is required.'),
  account_sid: Yup.string().required('Account Sid is required.'),
  auth_token: Yup.string().required('Authentication token is required.'),
  twilio_phone_no: Yup.string().required('Twilio phone number is required.'),
  twilio_phone_numbers_to_dial_valid: Yup.array().required('Phone numbers to dial are required.'),
});

export default TwilioSchema;
