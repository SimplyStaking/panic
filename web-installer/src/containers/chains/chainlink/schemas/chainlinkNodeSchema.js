import * as Yup from 'yup';
import { checkIfDoesNotContainsSquareBracket, checkSourceName } from 'utils/helpers';

const ChainlinkNodeSchema = (props) => Yup.object().shape({
  name: Yup.string()
    .test('unique-node-name', 'Node name is not unique.', (value) => {
      const {
        cosmosNodesConfig,
        substrateNodesConfig,
        systemConfig,
        reposConfig,
        chainlinkNodesConfig,
        dockerHubConfig,
        evmNodesConfig,
      } = props;

      return checkSourceName(value, ...[
        evmNodesConfig,
        chainlinkNodesConfig,
        cosmosNodesConfig,
        substrateNodesConfig,
        systemConfig,
        reposConfig,
        dockerHubConfig,
      ]);
    })
    .test('does-not-contain-square-bracket', 'Node name contains a square bracket',
      (value) => checkIfDoesNotContainsSquareBracket(value))
    .required('Node name is required.'),
});

export default ChainlinkNodeSchema;
