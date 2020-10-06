import { withFormik } from 'formik';
import { connect } from 'react-redux';
import KmsForm from '../../../components/chains/general/forms/kmsForm';
import KmsTable from '../../../components/chains/general/tables/kmsTable';
import { addKms, removeKms } from '../../../redux/actions/generalActions';
import KmsSchema from './schemas/kmsSchema';
import CosmosData from '../../../data/cosmos';

// This performs kms name validation, by checking if the kms name is already
// setup, and if the exporterUrl is provided
const Form = withFormik({
  mapPropsToErrors: () => ({
    kmsName: '',
    exporterUrl: '',
  }),
  mapPropsToValues: () => ({
    kmsName: '',
    exporterUrl: '',
    monitorKms: true,
  }),
  validationSchema: (props) => KmsSchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveKmsDetails, currentChain } = props;
    const payload = {
      parentId: currentChain,
      kmsName: values.kmsName,
      exporterUrl: values.exporterUrl,
      monitorKms: values.monitorKms,
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

export {
  KmsCosmosFormContainer,
  KmsCosmosTableContainer,
};
