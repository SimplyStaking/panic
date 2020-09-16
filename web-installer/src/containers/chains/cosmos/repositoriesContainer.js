import { withFormik } from 'formik';
import { connect } from 'react-redux';
import RepositoriesForm from '../../../components/chains/cosmos/forms/repositoriesForm';
import RepositoriesTable from '../../../components/chains/cosmos/tables/repositoriesTable';
import { addRepositoryCosmos, removeRepositoryCosmos } from '../../../redux/actions/cosmosChainsActions';
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
    const { saveRepositoryDetails } = props;
    const payload = {
      repoName: values.repoName,
      monitorRepo: values.monitorRepo,
    };
    saveRepositoryDetails(payload);
    resetForm();
  },
})(RepositoriesForm);

const mapStateToProps = (state) => ({
  cosmosConfigs: state.CosmosChainsReducer.cosmosConfigs,
  config: state.CosmosChainsReducer.config,
});

function mapDispatchToProps(dispatch) {
  return {
    saveRepositoryDetails: (details) => dispatch(addRepositoryCosmos(details)),
  };
}
function mapDispatchToPropsRemove(dispatch) {
  return {
    removeRepositoryDetails: (details) => dispatch(removeRepositoryCosmos(details)),
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
