import * as Yup from 'yup';
import { checkSourceName } from 'utils/helpers';

const RepositorySchema = (props) => Yup.object().shape({
  repo_name: Yup.string()
    .test('unique-repository-name', 'Name already exists.', (value) => {
      const {
        systemConfig,
        substrateNodesConfig,
        cosmosNodesConfig,
        reposConfig,
        chainlinkNodesConfig,
        dockerHubConfig,
        evmNodesConfig,
      } = props;

      return checkSourceName(
        value,
        ...[
          evmNodesConfig,
          chainlinkNodesConfig,
          cosmosNodesConfig,
          substrateNodesConfig,
          systemConfig,
          reposConfig,
          dockerHubConfig,
        ],
      );
    })
    .required('Repository name is required.'),
});

export default RepositorySchema;
