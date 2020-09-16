import * as Yup from 'yup';

const KMSSchema = (props) => Yup.object().shape({
  kmsName: Yup.string()
    .test(
      'unique-kms-name',
      'KMS name is not unique.',
      (value) => {
        const { substrateConfigs } = props;
        if (substrateConfigs.length === 0) {
          return true;
        }
        for (let i = 0; i < substrateConfigs.length; i += 1) {
          if (substrateConfigs[i].kmses.length === 0) {
            return true;
          }
          for (let j = 0; j < substrateConfigs[i].kmses.length; j += 1) {
            if (substrateConfigs[i].kmses[j] === value) {
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
