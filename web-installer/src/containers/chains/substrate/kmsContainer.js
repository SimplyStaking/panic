import { withFormik } from 'formik';
import { connect } from 'react-redux';
import KMSForm from '../../../components/chains/substrate/forms/kmsForm';
import KMSTable from '../../../components/chains/substrate/tables/kmsTable';
import { addKMSSubstrate, removeKMSSubstrate } from '../../../redux/actions/substrateChainsActions';
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
  substrateConfigs: state.SubstrateChainsReducer.substrateConfigs,
  config: state.SubstrateChainsReducer.config,
});

function mapDispatchToProps(dispatch) {
  return {
    saveKMSDetails: (details) => dispatch(addKMSSubstrate(details)),
  };
}
function mapDispatchToPropsRemove(dispatch) {
  return {
    removeKMSDetails: (details) => dispatch(removeKMSSubstrate(details)),
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
