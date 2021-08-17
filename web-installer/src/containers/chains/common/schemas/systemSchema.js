import * as Yup from 'yup';
import { checkSourceName } from 'utils/helpers';

const SystemSchema = (props) => Yup.object().shape({
  name: Yup.string()
    .test('unique-system-name', 'System name is not unique.', (value) => {
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
    .required('System name is required.'),
  exporter_url: Yup.string().required('Node Exporter URL is required.'),
});

export default SystemSchema;
