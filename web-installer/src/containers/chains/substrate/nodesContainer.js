import { withFormik } from 'formik';
import { connect } from 'react-redux';
import NodesForm from '../../../components/chains/substrate/forms/nodesForm';
import NodesTable from '../../../components/chains/substrate/tables/nodesTable';
import { addNodeSubstrate, removeNodeSubstrate } from '../../../redux/actions/substrateChainsActions';
import NodeSchema from './schemas/nodeSchema';

const Form = withFormik({
  mapPropsToErrors: () => ({
    substrateNodeName: '',
  }),
  mapPropsToValues: () => ({
    substrateNodeName: '',
    tendermintRPCURL: '',
    substrateRPCURL: '',
    prometheusURL: '',
    exporterURL: '',
    isValidator: false,
    monitorNode: true,
    isArchiveNode: true,
    useAsDataSource: true,
  }),
  validationSchema: (props) => NodeSchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveNodeDetails } = props;
    const payload = {
      substrateNodeName: values.substrateNodeName,
      tendermintRPCURL: values.tendermintRPCURL,
      substrateRPCURL: values.substrateRPCURL,
      prometheusURL: values.prometheusURL,
      exporterURL: values.exporterURL,
      isValidator: values.isValidator,
      monitorNode: values.monitorNode,
      isArchiveNode: values.isArchiveNode,
      useAsDataSource: values.useAsDataSource,
    };
    saveNodeDetails(payload);
    resetForm();
  },
})(NodesForm);

const mapStateToProps = (state) => ({
  substrateConfigs: state.SubstrateChainsReducer.substrateConfigs,
  config: state.SubstrateChainsReducer.config,
});

function mapDispatchToProps(dispatch) {
  return {
    saveNodeDetails: (details) => dispatch(addNodeSubstrate(details)),
  };
}

function mapDispatchToPropsRemove(dispatch) {
  return {
    removeNodeDetails: (details) => dispatch(removeNodeSubstrate(details)),
  };
}

const NodesFormContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Form);

const NodesTableContainer = connect(
  mapStateToProps,
  mapDispatchToPropsRemove,
)(NodesTable);

export {
  NodesFormContainer,
  NodesTableContainer,
};
