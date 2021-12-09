import * as Yup from 'yup';
import { checkChannelName } from 'utils/helpers';

/*
  SlackSchema takes in props and returns a Yup validation object,
  this object performs validation on the individual values in side the form,
  and returns error messages if any.

  .test function is used to create a custom validation, in this case
  we are checking through passed props if the Name that is entered into the
  form is unique or not, this will make the current states not overridable.

  .string makes sure that the entered input is in the string format.
  .number makes sure that the entered input is in numeric format.
  .typeError returns the specified error message if the input is not numeric.
*/
const SlackSchema = (props) => Yup.object().shape({
  channel_name: Yup.string()
    .test('unique-channel-name', 'Slack Channel Name is not unique.', (value) => {
      const {
        emails, opsGenies, pagerDuties, telegrams, twilios, slacks,
      } = props;
      return checkChannelName(
        value,
        ...[emails, opsGenies, pagerDuties, telegrams, twilios, slacks],
      );
    })
    .required('Slack Channel Name is required.'),
  bot_token: Yup.string().required('Bot token is required.'),
  app_token: Yup.string().required('App-Level token is required.'),
  bot_channel_id: Yup.string().required('Bot channel ID is required.'),
});

export default SlackSchema;
