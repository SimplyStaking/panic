import * as Yup from 'yup';

const ChainNameSchema = (props) => Yup.object().shape({
  chainName: Yup.string()
    .test(
      'unique-chain-name',
      'Chain name is not unique.',
      (value) => {
        const { cosmosChains } = props;
        if (cosmosChains.length === 0) {
          return true;
        }
        for (let i = 0; i < cosmosChains.length; i += 1) {
          if (cosmosChains[i].chainName === value) {
            return false;
          }
        }
        return true;
      },
    )
    .required('Chain name is required.'),
});

export default ChainNameSchema;
