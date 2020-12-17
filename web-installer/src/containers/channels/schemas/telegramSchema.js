import * as Yup from 'yup';

/*
  TelegramSchame takes in props and returns a Yup validation object,
  this object performs validation on the individual values in side the form,
  and returns error messages if any.

  .test function is used to create a custom validation, in this case
  we are checking through passed props if the Bot Name that is entered into the
  form is unique or not, this will make the current states not overridable.

  .string makes sure that the entered input is in the string format.
  .number makes sure that the entered input is in numeric format.
  .typeError returns the specified error message if the input is not numeric.
*/
const TelegramSchema = (props) => Yup.object().shape({
  channel_name: Yup.string()
    .test(
      'unique-bot-name',
      'Bot Name is not unique.',
      (value) => {
        const {
          emails, opsGenies, pagerDuties, telegrams, twilios,
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
        return true;
      },
    )
    .required('Bot name is required.'),
  bot_token: Yup.string()
    .required('Bot token is required.'),
  chat_id: Yup.number()
    .typeError('Chat ID must be numeric.')
    .required('Chat ID number is required.'),
});

export default TelegramSchema;
