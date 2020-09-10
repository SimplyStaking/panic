import * as Yup from 'yup';

const ChainNameSchema = (props) => Yup.object().shape({
  chainName: Yup.string()
    .test(
      'unique-chain-name',
      'Chain name is not unique.',
      (value) => {
        const { cosmosConfigs } = props;
        if (cosmosConfigs.length === 0) {
          return true;
        }
        for (let i = 0; i < cosmosConfigs.length; i += 1) {
          if (cosmosConfigs[i].config.chainName === value) {
            return false;
          }
        }
        return true;
      },
    )
    .required('Chain name is required.'),
});

export default ChainNameSchema;
