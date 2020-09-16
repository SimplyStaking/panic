import * as Yup from 'yup';

const RepositorySchema = (props) => Yup.object().shape({
  repoName: Yup.string()
    .test(
      'unique-repository-name',
      'Repository is arleady exists.',
      (value) => {
        const { substrateConfigs } = props;
        if (substrateConfigs.length === 0) {
          return true;
        }
        for (let i = 0; i < substrateConfigs.length; i += 1) {
          if (substrateConfigs.repositories.length === 0) {
            return true;
          }
          for (let j = 0; j < substrateConfigs[i].repositories.length; j += 1) {
            if (substrateConfigs[i].repositories[j] === value) {
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
