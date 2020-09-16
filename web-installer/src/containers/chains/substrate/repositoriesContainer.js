import { withFormik } from 'formik';
import { connect } from 'react-redux';
import RepositoriesForm from '../../../components/chains/substrate/forms/repositoriesForm';
import RepositoriesTable from '../../../components/chains/substrate/tables/repositoriesTable';
import { addRepositorySubstrate, removeRepositorySubstrate } from '../../../redux/actions/substrateChainsActions';
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
  substrateConfigs: state.SubstrateChainsReducer.substrateConfigs,
  config: state.SubstrateChainsReducer.config,
});

function mapDispatchToProps(dispatch) {
  return {
    saveRepositoryDetails:
      (details) => dispatch(addRepositorySubstrate(details)),
  };
}
function mapDispatchToPropsRemove(dispatch) {
  return {
    removeRepositoryDetails:
      (details) => dispatch(removeRepositorySubstrate(details)),
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
