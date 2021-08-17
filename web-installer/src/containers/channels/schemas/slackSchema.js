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
    .test('unique-bot-name', 'Slack Bot Name is not unique.', (value) => {
      const {
        emails, opsGenies, pagerDuties, telegrams, twilios, slacks,
      } = props;
      return checkChannelName(
        value,
        ...[emails, opsGenies, pagerDuties, telegrams, twilios, slacks],
      );
    })
    .required('Slack Bot Name is required.'),
  token: Yup.string().required('Token is required.'),
  chat_name: Yup.string().required('Chat name is required.'),
});

export default SlackSchema;
