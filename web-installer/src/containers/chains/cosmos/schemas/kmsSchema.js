import * as Yup from 'yup';

const KMSSchema = (props) => Yup.object().shape({
  kmsName: Yup.string()
    .test(
      'unique-kms-name',
      'KMS name is not unique.',
      (value) => {
        const { cosmosConfigs } = props;
        if (cosmosConfigs.length === 0) {
          return true;
        }
        for (let i = 0; i < cosmosConfigs.length; i += 1) {
          if (cosmosConfigs.config.kmses.length === 0) {
            return true;
          }
          for (let j = 0; j < cosmosConfigs[i].config.kmses.length; j += 1) {
            if (cosmosConfigs[i].config.kmses[j] === value) {
              return false;
            }
          }
        }
        return true;
      },
    )
    .required('KMS name is required.'),
  exporterURL: Yup.string()
    .required('Node Exporter Url is required.'),
});

export default KMSSchema;
