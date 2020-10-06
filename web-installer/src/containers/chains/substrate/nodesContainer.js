import { withFormik } from 'formik';
import { connect } from 'react-redux';
import NodesForm from '../../../components/chains/substrate/forms/nodesForm';
import NodesTable from '../../../components/chains/substrate/tables/nodesTable';
import { addNodeSubstrate, removeNodeSubstrate } from '../../../redux/actions/substrateActions';
import NodeSchema from './schemas/nodeSchema';

const Form = withFormik({
  mapPropsToErrors: () => ({
    substrateNodeName: '',
  }),
  mapPropsToValues: () => ({
    substrateNodeName: '',
    nodeWSURL: '',
    telemetryURL: '',
    prometheusURL: '',
    exporterUrl: '',
    stashAddress: '',
    isValidator: false,
    monitorNode: true,
    isArchiveNode: true,
    useAsDataSource: true,
  }),
  validationSchema: (props) => NodeSchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveNodeDetails, currentChain } = props;
    const payload = {
      parentId: currentChain,
      substrateNodeName: values.substrateNodeName,
      nodeWSURL: values.nodeWSURL,
      telemetryURL: values.telemetryURL,
      prometheusURL: values.prometheusURL,
      exporterUrl: values.exporterUrl,
      stashAddress: values.stashAddress,
      isValidator: values.isValidator,
      monitorNode: values.monitorNode,
      isArchiveNode: values.isArchiveNode,
      useAsDataSource: values.useAsDataSource,
    };
    saveNodeDetails(payload);
    resetForm();
  },
})(NodesForm);

// Need all of the configuration, including the current chain id we are setting
// up.
const mapStateToProps = (state) => ({
  currentChain: state.CurrentSubstrateChain,
  chainConfig: state.SubstrateChainsReducer,
  nodesConfig: state.SubstrateNodesReducer,
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
