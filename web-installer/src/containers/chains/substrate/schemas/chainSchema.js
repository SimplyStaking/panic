import * as Yup from 'yup';

const ChainNameSchema = (props) => Yup.object().shape({
  chainName: Yup.string()
    .test(
      'unique-chain-name',
      'Chain name is not unique.',
      (value) => {
        const { substrateConfigs } = props;
        if (substrateConfigs.length === 0) {
          return true;
        }
        for (let i = 0; i < substrateConfigs.length; i += 1) {
          if (substrateConfigs[i].chainName === value) {
            return false;
          }
        }
        return true;
      },
    )
    .required('Chain name is required.'),
});

export default ChainNameSchema;
