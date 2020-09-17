import { withFormik } from 'formik';
import { connect } from 'react-redux';
import SystemForm from '../../components/general/forms/systemForm';
import SystemTable from '../../components/general/tables/systemTable';
import { addSystem, removeSystem } from '../../redux/actions/generalActions';
import SystemSchema from './schemas/systemSchema';

const Form = withFormik({
  mapPropsToErrors: () => ({
    name: '',
    exporterURL: '',
  }),
  mapPropsToValues: () => ({
    name: '',
    exporterURL: '',
    enabled: true,
  }),
  validationSchema: (props) => SystemSchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveSystemDetails } = props;
    const payload = {
      name: values.name,
      exporterURL: values.exporterURL,
      enabled: values.enabled,
    };
    saveSystemDetails(payload);
    resetForm();
  },
})(SystemForm);

const mapStateToProps = (state) => ({
  systems: state.GeneralReducer.systems,
});

function mapDispatchToProps(dispatch) {
  return {
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
