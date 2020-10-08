import * as Yup from 'yup';

const RepositorySchema = (props) => Yup.object().shape({
  repoName: Yup.string()
    .test(
      'unique-repository-name',
      'Repository arleady exists.',
      (value) => {
        const { reposConfig } = props;

        // If repos are empty no need to validate anything
        if (reposConfig.allIds.length === 0) {
          return true;
        }

        for (let i = 0; i < reposConfig.allIds.length; i += 1) {
          if (reposConfig.byId[reposConfig.allIds[i]].repoName === value) {
            return false;
          }
        }

        return true;
      },
    )
    .required('Repository name is required.'),
});

export default RepositorySchema;
