import * as Yup from 'yup';

const OpsGenieSchema = (props) => Yup.object().shape({
  channel_name: Yup.string()
    .test(
      'unique-config-name',
      'OpsGenie config name is not unique.',
      (value) => {
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
          if (
            pagerDuties.byId[pagerDuties.allIds[i]].channel_name === value
          ) {
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
      },
    )
    .required('Config name is required.'),
  api_token: Yup.string().required('API token is required.'),
});

export default OpsGenieSchema;
