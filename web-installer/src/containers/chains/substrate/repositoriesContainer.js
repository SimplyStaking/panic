import { withFormik } from 'formik';
import { connect } from 'react-redux';
import RepositoriesForm from '../../../components/chains/substrate/forms/repositoriesForm';
import RepositoriesTable from '../../../components/chains/substrate/tables/repositoriesTable';
import { addRepository, removeRepository } from '../../../redux/actions/generalActions';
import RepositorySchema from './schemas/repositorySchema';

const Form = withFormik({
  mapPropsToErrors: () => ({
    repoName: '',
  }),
  mapPropsToValues: () => ({
    repoName: '',
    monitorRepo: true,
  }),
  validationSchema: (props) => RepositorySchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveRepositoryDetails, currentChain } = props;
    const payload = {
      parentId: currentChain,
      repoName: values.repoName,
      monitorRepo: values.monitorRepo,
    };
    saveRepositoryDetails(payload);
    resetForm();
  },
})(RepositoriesForm);

const mapStateToProps = (state) => ({
  currentChain: state.CurrentSubstrateChain,
  chainConfig: state.SubstrateChainsReducer,
  reposConfig: state.RepositoryReducer,
});

function mapDispatchToProps(dispatch) {
  return {
    saveRepositoryDetails:
      (details) => dispatch(addRepository(details)),
  };
}
function mapDispatchToPropsRemove(dispatch) {
  return {
    removeRepositoryDetails:
      (details) => dispatch(removeRepository(details)),
  };
}

const RepositoriesFormContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Form);

const RepositoriesTableContainer = connect(
  mapStateToProps,
  mapDispatchToPropsRemove,
)(RepositoriesTable);

export {
  RepositoriesFormContainer,
  RepositoriesTableContainer,
};
