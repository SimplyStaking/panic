import { withFormik } from 'formik';
import { connect } from 'react-redux';
import KmsForm from 'components/chains/common/forms/kmsForm';
import KmsTable from 'components/chains/common/tables/kmsTable';
import { addKms, removeKms } from 'redux/actions/generalActions';
import CosmosData from 'data/cosmos';
import KmsSchema from './schemas/kmsSchema';

// This performs kms name validation, by checking if the kms name is already
// setup, and if the exporter_url is provided
const Form = withFormik({
  mapPropsToErrors: () => ({
    kms_name: '',
    exporter_url: '',
  }),
  mapPropsToValues: () => ({
    kms_name: '',
    exporter_url: '',
    monitor_kms: true,
  }),
  validationSchema: (props) => KmsSchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveKmsDetails, currentChain } = props;
    const payload = {
      parent_id: currentChain,
      kms_name: values.kms_name,
      exporter_url: values.exporter_url,
      monitor_kms: values.monitor_kms,
    };
    saveKmsDetails(payload);
    resetForm();
  },
})(KmsForm);

// ------------------------- Cosmos Based Chain Data --------------------

// Cosmos redux data that will be used to control the kms form and populate
// the kms table.
const mapCosmosStateToProps = (state) => ({
  currentChain: state.CurrentCosmosChain,
  chainConfig: state.CosmosChainsReducer,
  kmsConfig: state.KmsReducer,
  data: CosmosData,
});

// Functions to be used in the Cosmos Kms form to save the form's details
function mapDispatchToProps(dispatch) {
  return {
    saveKmsDetails: (details) => dispatch(addKms(details)),
  };
}

// Function to be used in the Cosmos Kms table to delete the saved details
// from state
function mapDispatchToPropsRemove(dispatch) {
  return {
    removeKmsDetails: (details) => dispatch(removeKms(details)),
  };
}

// Combine cosmos state and dispatch functions to the kms form
const KmsCosmosFormContainer = connect(
  mapCosmosStateToProps,
  mapDispatchToProps,
)(Form);

// Combine cosmos state and dispatch functions to the kms table
const KmsCosmosTableContainer = connect(
  mapCosmosStateToProps,
  mapDispatchToPropsRemove,
)(KmsTable);

export { KmsCosmosFormContainer, KmsCosmosTableContainer };
