import * as Yup from 'yup';

const SystemSchema = (props) => Yup.object().shape({
  name: Yup.string()
    .test(
      'unique-system-name',
      'System config name is not unique.',
      (value) => {
        const { systems } = props;
        if (systems.allIds.length === 0) {
          return true;
        }
        for (let i = 0; i < systems.allIds.length; i += 1) {
          if (systems.byId[systems.allIds[i]].name === value) {
            return false;
          }
        }
        return true;
      },
    )
    .required('Config name is required.'),
  exporterURL: Yup.string()
    .required('Node Exporter Url is required.'),
});

export default SystemSchema;
