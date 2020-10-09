import * as Yup from 'yup';

const TwilioSchema = (props) => Yup.object().shape({
  configName: Yup.string()
    .test(
      'unique-config-name',
      'Twilio config name is not unique.',
      (value) => {
        const { twilios } = props;
        if (twilios.allIds.length === 0) {
          return true;
        }
        for (let i = 0; i < twilios.allIds.length; i += 1) {
          if (twilios.byId[twilios.allIds[i]].configName === value) {
            return false;
          }
        }
        return true;
      },
    )
    .required('Config name is required.'),
  accountSid: Yup.string()
    .required('Account Sid is required.'),
  authToken: Yup.string()
    .required('Authentication token is required.'),
  twilioPhoneNo: Yup.string()
    .required('Twilio phone number is required.'),
  twilioPhoneNumbersToDialValid: Yup.array()
    .required('Phone numbers to dial are required.'),
});

export default TwilioSchema;
