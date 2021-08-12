import * as Yup from 'yup';

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
      for (let i = 0; i < emails.allIds.length; i += 1) {
        if (emails.byId[emails.allIds[i]].channel_name === value) {
          return false;
        }
      }
      for (let i = 0; i < opsGenies.allIds.length; i += 1) {
        if (opsGenies.byId[opsGenies.allIds[i]].channel_name === value) {
          return false;
        }
      }
      for (let i = 0; i < pagerDuties.allIds.length; i += 1) {
        if (pagerDuties.byId[pagerDuties.allIds[i]].channel_name === value) {
          return false;
        }
      }
      for (let i = 0; i < telegrams.allIds.length; i += 1) {
        if (telegrams.byId[telegrams.allIds[i]].channel_name === value) {
          return false;
        }
      }
      for (let i = 0; i < twilios.allIds.length; i += 1) {
        if (twilios.byId[twilios.allIds[i]].channel_name === value) {
          return false;
        }
      }
      for (let i = 0; i < slacks.allIds.length; i += 1) {
        if (slacks.byId[slacks.allIds[i]].channel_name === value) {
          return false;
        }
      }
      return true;
    })
    .required('Slack Bot Name is required.'),
  bot_token: Yup.string().required('Bot token is required.'),
  app_token: Yup.string().required('App-Level token is required.'),
  bot_channel_id: Yup.string().required('Bot channel ID is required.'),
});

export default SlackSchema;
