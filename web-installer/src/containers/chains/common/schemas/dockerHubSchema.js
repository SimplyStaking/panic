import * as Yup from 'yup';
import { checkSourceName } from 'utils/helpers';

const DockerHubSchema = (props) => Yup.object().shape({
  name: Yup.string()
    .test('unique-dockerHub-name', 'Name already exists.', (value) => {
      const {
        systemConfig,
        substrateNodesConfig,
        cosmosNodesConfig,
        reposConfig,
        dockerHubConfig,
        chainlinkNodesConfig,
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
    .required('DockerHub name is required.'),
});

export default DockerHubSchema;
