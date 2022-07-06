import * as Yup from 'yup';
import { checkChannelName, checkIfDoesNotContainsSquareBracket } from 'utils/helpers';

const OpsGenieSchema = (props) => Yup.object().shape({
  channel_name: Yup.string()
    .test(
      'unique-config-name',
      'OpsGenie config name is not unique.',
      (value) => {
        const {
          emails, opsGenies, pagerDuties, telegrams, twilios, slacks,
        } = props;
        return checkChannelName(
          value,
          ...[emails, opsGenies, pagerDuties, telegrams, twilios, slacks],
        );
      },
    )
    .test('does-not-contain-square-bracket', 'OpsGenie config name contains a square bracket',
      (value) => checkIfDoesNotContainsSquareBracket(value))
    .required('Config name is required.'),
  api_token: Yup.string().required('API token is required.'),
});

export default OpsGenieSchema;
