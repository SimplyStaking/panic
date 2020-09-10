import * as Yup from 'yup';

const RepositorySchema = (props) => Yup.object().shape({
  repoName: Yup.string()
    .test(
      'unique-repository-name',
      'Repository is arleady exists.',
      (value) => {
        const { cosmosConfigs } = props;
        if (cosmosConfigs.length === 0) {
          return true;
        }
        for (let i = 0; i < cosmosConfigs.length; i += 1) {
          if (cosmosConfigs.config.nodes.length === 0) {
            return true;
          }
          for (let j = 0; j < cosmosConfigs[i].config.repositories.length; j += 1) {
            if (cosmosConfigs[i].config.repositories[j] === value) {
              return false;
            }
          }
        }
        return true;
      },
    )
    .required('Repository name is required.'),
});

export default RepositorySchema;
