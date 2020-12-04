import * as Yup from 'yup';

const KmsSchema = (props) => Yup.object().shape({
  kms_name: Yup.string()
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
          if (kmsConfig.byId[kmsConfig.allIds[i]].kms_name === value) {
            return false;
          }
        }

        return true;
      },
    )
    .required('KMS name is required.'),
  exporter_url: Yup.string()
    .required('Node Exporter Url is required.'),
});

export default KmsSchema;
