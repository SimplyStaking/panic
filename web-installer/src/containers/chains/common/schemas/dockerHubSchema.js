import * as Yup from 'yup';
import { checkDockerHubRepoExists } from 'utils/helpers';

const DockerHubSchema = (props) => Yup.object().shape({
  name: Yup.string()
    .test('unique-dockerHub-name', 'DockerHub repo already exists.', (value) => {
      const {
        dockerHubConfig,
      } = props;

      return checkDockerHubRepoExists(
        value,
        dockerHubConfig,
      );
    })
    .matches('^[a-z+-0-9]+\\/[a-z+-0-9]+$|^[a-z+-0-9]+$', 'Name must be in the form \'simplyvc/panic\' or \'panic\'.')
    .required('DockerHub name is required.'),
});

export default DockerHubSchema;
