import * as Yup from 'yup';
import { checkGitHubRepoExists } from 'utils/helpers';

const RepositorySchema = (props) => Yup.object().shape({
  repo_name: Yup.string()
    .test('unique-repository-name', 'GitHub repo already exists.', (value) => {
      const {
        reposConfig,
      } = props;

      return checkGitHubRepoExists(
        value,
        reposConfig,
      );
    })
    .required('Repository name is required.'),
});

export default RepositorySchema;
