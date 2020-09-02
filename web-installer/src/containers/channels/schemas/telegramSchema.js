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
  botName: Yup.string()
    .test(
      'unique-bot-name',
      'Bot Name is not unique.',
      (value) => {
        const { telegrams } = props;
        if (telegrams.length === 0) {
          return true;
        }
        for (let i = 0; i < telegrams.length; i += 1) {
          if (telegrams[i].botName === value) {
            return false;
          }
        }
        return true;
      },
    )
    .required('Bot name is required.'),
  botToken: Yup.string()
    .required('Bot token is required.'),
  chatID: Yup.number()
    .typeError('Chat ID must be numeric.')
    .required('Chat ID number is required.'),
});

export default TelegramSchema;
