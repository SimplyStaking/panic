import * as Yup from 'yup';

const GithubSchema = (props) => Yup.object().shape({
  repoName: Yup.string()
    .test(
      'unique-repository-name',
      'Repository arleady exists.',
      (value) => {
        const { repositories } = props;
        if (repositories.length === 0) {
          return true;
        }
        for (let i = 0; i < repositories.length; i += 1) {
          if (repositories[i].repoName.length === value) {
            return true;
          }
        }
        return true;
      },
    )
    .required('Repository name is required.'),
});

export default GithubSchema;
