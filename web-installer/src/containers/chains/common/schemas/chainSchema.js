import * as Yup from 'yup';

const ChainNameSchema = (props) => Yup.object().shape({
  chain_name: Yup.string()
    .test('unique-chain-name', 'Chain name is not unique.', (value) => {
      const { config, config2 } = props;
      if (config.allIds.length === 0) {
        return true;
      }
      for (let i = 0; i < config.allIds.length; i += 1) {
        if (config.byId[config.allIds[i]].chain_name === value) {
          return false;
        }
      }
      for (let i = 0; i < config2.allIds.length; i += 1) {
        if (config2.byId[config2.allIds[i]].chain_name === value) {
          return false;
        }
      }
      return true;
    })
    .required('Chain name is required.'),
});

export default ChainNameSchema;
