import { withFormik } from 'formik';
import { connect } from 'react-redux';
import RepositoryForm from '../../components/general/forms/repositoryForm';
import RepositoryTable from '../../components/general/tables/repositoryTable';
import { addRepository, removeRepository } from '../../redux/actions/generalActions';
import { GLOBAL } from '../../constants/constants';
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
      parentId: GLOBAL,
      repoName: values.repoName,
      monitorRepo: values.monitorRepo,
    };
    saveRepositoryDetails(payload);
    resetForm();
  },
})(RepositoryForm);

const mapStateToProps = (state) => ({
  config: state.GeneralReducer,
  repositories: state.RepositoryReducer,
});

function mapDispatchToProps(dispatch) {
  return {
    saveRepositoryDetails: (details) => dispatch(addRepository(details)),
  };
}

function mapDispatchToPropsRemove(dispatch) {
  return {
    removeRepositoryDetails: (details) => dispatch(removeRepository(details)),
  };
}

const RepositoryFormContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Form);

const RepositoryTableContainer = connect(
  mapStateToProps,
  mapDispatchToPropsRemove,
)(RepositoryTable);

export {
  RepositoryFormContainer,
  RepositoryTableContainer,
};
