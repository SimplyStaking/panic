import { withFormik } from 'formik';
import { connect } from 'react-redux';
import RepositoriesForm from '../../../components/chains/cosmos/forms/repositoriesForm';
import { addRepository } from '../../../redux/actions/chainsActions';
import RepositorySchema from './schemas/repositorySchema';

const Form = withFormik({
  mapPropsToErrors: () => ({
    repoName: '',
  }),
  mapPropsToValues: () => ({
    repoName: '',
  }),
  validationSchema: (props) => RepositorySchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveRepositoryDetails } = props;
    const payload = {
      repoName: values.repoName,
    };
    saveRepositoryDetails(payload);
    resetForm();
  },
})(RepositoriesForm);

const mapStateToProps = (state) => ({
  cosmosChains: state.ChainsReducer.cosmosChains,
});

function mapDispatchToProps(dispatch) {
  return {
    saveRepositoryDetails: (details) => dispatch(addRepository(details)),
  };
}

const RepositoriesFormContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Form);

export default RepositoriesFormContainer;
