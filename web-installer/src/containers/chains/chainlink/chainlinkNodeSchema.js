import * as Yup from 'yup';
import Web3 from 'web3';

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
      for (let i = 0; i < dockerHubConfig.allIds.length; i += 1) {
        if (dockerHubConfig.byId[dockerHubConfig.allIds[i]].repo_name === value) {
          return false;
        }
      }
      return true;
    })
    .required('Node name is required.'),
  node_address: Yup.array()
    .of(Yup.string()
      .test('ethereum-address-validation', 'One or more provided addresses are not valid!.', (value) => {
        if (Web3.utils.isAddress(value)) {
          return true;
        }
        return false;
      })),
});

export default ChainlinkNodeSchema;
