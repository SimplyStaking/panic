import * as Yup from 'yup';
import { BLACKLIST } from 'constants/constants';

const ChainlinkNodeSchema = (props) => Yup.object().shape({
  name: Yup.string()
    .test('unique-node-name', 'Node name is not unique.', (value) => {
      const {
        cosmosNodesConfig, substrateNodesConfig, systemConfig, reposConfig,
        chainlinkNodesConfig, dockerConfig,
      } = props;

      for (let i = 0; i < chainlinkNodesConfig.allIds.length; i += 1) {
        if (chainlinkNodesConfig.byId[chainlinkNodesConfig.allIds[i]].name === value) {
          return false;
        }
      }
      for (let i = 0; i < cosmosNodesConfig.allIds.length; i += 1) {
        if (cosmosNodesConfig.byId[cosmosNodesConfig.allIds[i]].name === value) {
          return false;
        }
      }
      for (let i = 0; i < substrateNodesConfig.allIds.length; i += 1) {
        if (substrateNodesConfig.byId[substrateNodesConfig.allIds[i]].name === value) {
          return false;
        }
      }
      for (let i = 0; i < systemConfig.allIds.length; i += 1) {
        if (systemConfig.byId[systemConfig.allIds[i]].name === value) {
          return false;
        }
      }
      for (let i = 0; i < reposConfig.allIds.length; i += 1) {
        if (reposConfig.byId[reposConfig.allIds[i]].repo_name === value) {
          return false;
        }
      }
      for (let i = 0; i < dockerConfig.allIds.length; i += 1) {
        if (dockerConfig.byId[dockerConfig.allIds[i]].repo_name === value) {
          return false;
        }
      }
      return true;
    })
    .required('Node name is required.'),
  prometheus_url: Yup.array()
    .of(Yup.string().test(
      'localhost',
      '127.0.0.1 is not allowed for security reasons.',
      (value) => {
        if (BLACKLIST.find((a) => value.includes(a))) {
          return false;
        }
        return true;
      },
    ))
    .required('Prometheus URL is required.'),
});

export default ChainlinkNodeSchema;
