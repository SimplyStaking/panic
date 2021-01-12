import * as Yup from 'yup';

const RepositorySchema = (props) => Yup.object().shape({
  repo_name: Yup.string()
    .test('unique-repository-name', 'Name already exists.', (value) => {
      const { systemConfig, nodesConfig, nodesConfig2, reposConfig } = props;

      for (let i = 0; i < nodesConfig.allIds.length; i += 1) {
        if (nodesConfig.byId[nodesConfig.allIds[i]].name === value) {
          return false;
        }
      }
      for (let i = 0; i < nodesConfig2.allIds.length; i += 1) {
        if (nodesConfig2.byId[nodesConfig2.allIds[i]].name === value) {
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

      return true;
    })
    .required('Repository name is required.'),
});

export default RepositorySchema;
