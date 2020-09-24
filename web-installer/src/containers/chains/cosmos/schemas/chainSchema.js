import * as Yup from 'yup';

const ChainNameSchema = (props) => Yup.object().shape({
  chainName: Yup.string()
    .test(
      'unique-chain-name',
      'Chain name is not unique.',
      (value) => {
        const { config } = props;
        if (config.allIds.length === 0) {
          return true;
        }
        for (let i = 0; i < config.allIds.length; i += 1) {
          if (config.byId[config.allIds[i]] === value) {
            return false;
          }
        }
        return true;
      },
    )
    .required('Chain name is required.'),
});

export default ChainNameSchema;
