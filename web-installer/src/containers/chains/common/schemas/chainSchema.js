import * as Yup from 'yup';
import { checkChainName, checkIfDoesNotContainsSquareBracket } from 'utils/helpers';

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
    .test('does-not-contain-square-bracket', 'Chain name contains a square bracket',
      (value) => checkIfDoesNotContainsSquareBracket(value))
    .required('Chain name is required.'),
});

export default ChainNameSchema;
