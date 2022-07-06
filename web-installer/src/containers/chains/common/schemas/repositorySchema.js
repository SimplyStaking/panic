import * as Yup from 'yup';
import { checkGitHubRepoExists, checkIfDoesNotContainsSquareBracket } from 'utils/helpers';

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
    .test('does-not-contain-square-bracket', 'GitHub repo name contains a square bracket',
      (value) => checkIfDoesNotContainsSquareBracket(value))
    .required('Repository name is required.'),
});

export default RepositorySchema;
