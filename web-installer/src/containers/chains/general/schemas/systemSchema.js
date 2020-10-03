import * as Yup from 'yup';

const SystemSchema = (props) => Yup.object().shape({
  name: Yup.string()
    .test(
      'unique-system-name',
      'System name is not unique.',
      (value) => {
        const { systemConfig } = props;

        // If systems are empty no need to validate anything
        if (systemConfig.allIds.length === 0) {
          return true;
        }

        for (let i = 0; i < systemConfig.allIds.length; i += 1) {
          if (systemConfig.byId[systemConfig.allIds[i]].name === value) {
            return false;
          }
        }

        return true;
      },
    )
    .required('System name is required.'),
  exporterURL: Yup.string()
    .required('Node Exporter Url is required.'),
});

export default SystemSchema;
