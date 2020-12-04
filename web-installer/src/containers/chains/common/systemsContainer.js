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
    exporter_url: '',
  }),
  mapPropsToValues: () => ({
    name: '',
    exporter_url: '',
    monitor_system: true,
  }),
  validationSchema: (props) => SystemSchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveSystemDetails } = props;
    const payload = {
      parent_id: GLOBAL,
      name: values.name,
      exporter_url: values.exporter_url,
      monitor_system: values.monitor_system,
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
