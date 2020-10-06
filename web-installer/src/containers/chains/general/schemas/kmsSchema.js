import * as Yup from 'yup';

const KmsSchema = (props) => Yup.object().shape({
  kmsName: Yup.string()
    .test(
      'unique-kms-name',
      'KMS name is not unique.',
      (value) => {
        const { kmsConfig } = props;

        // If kmses are empty no need to validate anything
        if (kmsConfig.allIds.length === 0) {
          return true;
        }

        for (let i = 0; i < kmsConfig.allIds.length; i += 1) {
          if (kmsConfig.byId[kmsConfig.allIds[i]].kmsName === value) {
            return false;
          }
        }

        return true;
      },
    )
    .required('KMS name is required.'),
  exporterUrl: Yup.string()
    .required('Node Exporter Url is required.'),
});

export default KmsSchema;
