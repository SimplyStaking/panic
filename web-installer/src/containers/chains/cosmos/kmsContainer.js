import { withFormik } from 'formik';
import { connect } from 'react-redux';
import KMSForm from '../../../components/chains/cosmos/forms/kmsForm';
import KMSTable from '../../../components/chains/cosmos/tables/kmsTable';
import { addKMSCosmos, removeKMSCosmos } from '../../../redux/actions/cosmosChainsActions';
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
    const { saveKMSDetails } = props;
    const payload = {
      kmsName: values.kmsName,
      exporterURL: values.exporterURL,
      monitorKMS: values.monitorKMS,
    };
    saveKMSDetails(payload);
    resetForm();
  },
})(KMSForm);

const mapStateToProps = (state) => ({
  cosmosConfigs: state.CosmosChainsReducer.cosmosConfigs,
  config: state.CosmosChainsReducer.config,
});

function mapDispatchToProps(dispatch) {
  return {
    saveKMSDetails: (details) => dispatch(addKMSCosmos(details)),
  };
}
function mapDispatchToPropsRemove(dispatch) {
  return {
    removeKMSDetails: (details) => dispatch(removeKMSCosmos(details)),
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
