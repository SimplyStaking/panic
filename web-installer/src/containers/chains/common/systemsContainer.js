import { withFormik } from 'formik';
import { connect } from 'react-redux';
import SystemForm from 'components/chains/common/forms/systemForm';
import SystemTable from 'components/chains/common/tables/systemTable';
import { addSystem, removeSystem } from 'redux/actions/generalActions';
import { changeStep, changePage } from 'redux/actions/pageActions';
import { GLOBAL } from 'constants/constants';
import SystemSchema from './schemas/systemSchema';

// Form validation, check if the system name is unique and if the exporter
// URL was provided.
const Form = withFormik({
  mapPropsToErrors: () => ({
    name: '',
    exporterUrl: '',
  }),
  mapPropsToValues: () => ({
    name: '',
    exporterUrl: '',
    monitorSystem: true,
  }),
  validationSchema: (props) => SystemSchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveSystemDetails } = props;
    const payload = {
      parentId: GLOBAL,
      name: values.name,
      exporterUrl: values.exporterUrl,
      monitorSystem: values.monitorSystem,
    };
    saveSystemDetails(payload);
    resetForm();
  },
})(SystemForm);

const mapStateToProps = (state) => ({
  currentChain: GLOBAL,
  config: state.GeneralReducer,
  systemConfig: state.SystemsReducer,
});

function mapDispatchToProps(dispatch) {
  return {
    stepChanger: (step) => dispatch(changeStep(step)),
    pageChanger: (page) => dispatch(changePage(page)),
    saveSystemDetails: (details) => dispatch(addSystem(details)),
  };
}
function mapDispatchToPropsRemove(dispatch) {
  return {
    removeSystemDetails: (details) => dispatch(removeSystem(details)),
  };
}

const SystemFormContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Form);

const SystemTableContainer = connect(
  mapStateToProps,
  mapDispatchToPropsRemove,
)(SystemTable);

export {
  SystemFormContainer,
  SystemTableContainer,
};
