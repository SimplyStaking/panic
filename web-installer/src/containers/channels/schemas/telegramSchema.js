import * as Yup from 'yup';

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
  chatID: Yup.number('Chat ID must be a number')
    .required('Chat ID number is required.'),
});

export default TelegramSchema;
