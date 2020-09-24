import { withFormik } from 'formik';
import { connect } from 'react-redux';
import KMSForm from '../../../components/chains/cosmos/forms/kmsForm';
import KMSTable from '../../../components/chains/cosmos/tables/kmsTable';
import { addKms, removeKms } from '../../../redux/actions/generalActions';
import KMSSchema from './schemas/kmsSchema';

const Form = withFormik({
  mapPropsToErrors: () => ({
    kmsName: '',
    exporterURL: '',
  }),
  mapPropsToValues: () => ({
    kmsName: '',
    exporterURL: '',
    monitorKMS: true,
  }),
  validationSchema: (props) => KMSSchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveKmsDetails, currentChain } = props;
    const payload = {
      parentId: currentChain,
      kmsName: values.kmsName,
      exporterURL: values.exporterURL,
      monitorKMS: values.monitorKMS,
    };
    saveKmsDetails(payload);
    resetForm();
  },
})(KMSForm);

const mapStateToProps = (state) => ({
  currentChain: state.CurrentCosmosChain,
  chainConfig: state.CosmosChainsReducer,
  kmsConfig: state.KmsReducer,
});

function mapDispatchToProps(dispatch) {
  return {
    saveKmsDetails: (details) => dispatch(addKms(details)),
  };
}
function mapDispatchToPropsRemove(dispatch) {
  return {
    removeKmsDetails: (details) => dispatch(removeKms(details)),
  };
}

const KMSFormContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Form);

const KMSTableContainer = connect(
  mapStateToProps,
  mapDispatchToPropsRemove,
)(KMSTable);

export {
  KMSFormContainer,
  KMSTableContainer,
};
