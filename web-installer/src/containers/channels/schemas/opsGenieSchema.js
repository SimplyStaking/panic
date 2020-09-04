import * as Yup from 'yup';

const OpsGenieSchema = (props) => Yup.object().shape({
  configName: Yup.string()
    .test(
      'unique-config-name',
      'OpsGenie config name is not unique.',
      (value) => {
        const { opsGenies } = props;
        if (opsGenies.length === 0) {
          return true;
        }
        for (let i = 0; i < opsGenies.length; i += 1) {
          if (opsGenies[i].configName === value) {
            return false;
          }
        }
        return true;
      },
    )
    .required('Config name is required.'),
  apiToken: Yup.string()
    .required('API token is required.'),
});

export default OpsGenieSchema;
