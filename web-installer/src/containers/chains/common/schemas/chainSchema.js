import * as Yup from 'yup';
import { checkChainName } from 'utils/helpers';

const ChainNameSchema = (props) => Yup.object().shape({
  chain_name: Yup.string()
    .test('unique-chain-name', 'Chain name is not unique.', (value) => {
      const {
        config, config2, config3, currentChain,
      } = props;

      if (currentChain) {
        if (config.byId[currentChain].chain_name === value) {
          return true;
        }
      }

      return checkChainName(value, ...[config, config2, config3]);
    })
    .required('Chain name is required.'),
});

export default ChainNameSchema;
