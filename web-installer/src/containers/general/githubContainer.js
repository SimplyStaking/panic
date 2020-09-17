import { withFormik } from 'formik';
import { connect } from 'react-redux';
import GithubForm from '../../components/general/forms/githubForm';
import GithubTable from '../../components/general/tables/githubTable';
import { addRepository, removeRepository } from '../../redux/actions/generalActions';
import GithubSchema from './schemas/githubSchema';

const Form = withFormik({
  mapPropsToErrors: () => ({
    name: '',
  }),
  mapPropsToValues: () => ({
    name: '',
    enabled: true,
  }),
  validationSchema: (props) => GithubSchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveGithubDetails } = props;
    const payload = {
      name: values.name,
      enabled: values.enabled,
    };
    saveGithubDetails(payload);
    resetForm();
  },
})(GithubForm);

const mapStateToProps = (state) => ({
  repositories: state.GeneralReducer.repositories,
});

function mapDispatchToProps(dispatch) {
  return {
    saveGithubDetails: (details) => dispatch(addRepository(details)),
  };
}

function mapDispatchToPropsRemove(dispatch) {
  return {
    removeGithubDetails: (details) => dispatch(removeRepository(details)),
  };
}

const GithubFormContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Form);

const GithubTableContainer = connect(
  mapStateToProps,
  mapDispatchToPropsRemove,
)(GithubTable);

export {
  GithubFormContainer,
  GithubTableContainer,
};
