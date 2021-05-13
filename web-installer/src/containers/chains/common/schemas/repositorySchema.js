import * as Yup from 'yup';

const RepositorySchema = (props) => Yup.object().shape({
  repo_name: Yup.string()
    .test('unique-repository-name', 'Name already exists.', (value) => {
      const {
        systemConfig, substrateNodesConfig, cosmosNodesConfig, reposConfig,
        chainlinkNodesConfig, dockerConfig,
      } = props;

      for (let i = 0; i < substrateNodesConfig.allIds.length; i += 1) {
        if (substrateNodesConfig.byId[substrateNodesConfig.allIds[i]].name === value) {
          return false;
        }
      }
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
        if (dockerConfig.byId[dockerConfig.allIds[i]].name === value) {
          return false;
        }
      }
      return true;
    })
    .required('Repository name is required.'),
});

export default RepositorySchema;
