import { withFormik } from 'formik';
import { connect } from 'react-redux';
import NodesForm from '../../../components/chains/substrate/forms/nodesForm';
import NodesTable from '../../../components/chains/substrate/tables/nodesTable';
import { addNodeSubstrate, removeNodeSubstrate } from
  '../../../redux/actions/substrateActions';
import NodeSchema from './schemas/nodeSchema';
import SubstrateData from '../../../data/substrate';

// This performs substrate node name validation, by checking if the node name
// already exists under the same chain being configured.
const Form = withFormik({
  mapPropsToErrors: () => ({
    substrateNodeName: '',
  }),
  mapPropsToValues: () => ({
    substrateNodeName: '',
    nodeWsUrl: '',
    telemetryUrl: '',
    prometheusUrl: '',
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
      nodeWsUrl: values.nodeWsUrl,
      telemetryUrl: values.telemetryUrl,
      prometheusUrl: values.prometheusUrl,
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

// ------------------------- Substrate Based Chain Data --------------------

// Substrate redux data that will be used to control the node form.
const mapStateToProps = (state) => ({
  currentChain: state.CurrentSubstrateChain,
  chainConfig: state.SubstrateChainsReducer,
  nodesConfig: state.SubstrateNodesReducer,
  data: SubstrateData,
});

// Functions to be used in the Substrate Node form to save the form's details
function mapDispatchToProps(dispatch) {
  return {
    saveNodeDetails: (details) => dispatch(addNodeSubstrate(details)),
  };
}

// Functions to be used in the Substrate Nodes table to delete the saved details
// from state
function mapDispatchToPropsRemove(dispatch) {
  return {
    removeNodeDetails: (details) => dispatch(removeNodeSubstrate(details)),
  };
}

// Combine substrate state and dispatch functions to the node form
const NodesFormContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Form);

// Combine substrate state and dispatch functions to the node table
const NodesTableContainer = connect(
  mapStateToProps,
  mapDispatchToPropsRemove,
)(NodesTable);

export {
  NodesFormContainer,
  NodesTableContainer,
};
