import { withFormik } from 'formik';
import { connect } from 'react-redux';
import NodesForm from 'components/chains/substrate/forms/nodesForm';
import NodesTable from 'components/chains/substrate/tables/nodesTable';
import {
  addNodeSubstrate,
  removeNodeSubstrate,
} from 'redux/actions/substrateActions';
import SubstrateData from 'data/substrate';
import NodeSchema from '../common/schemas/nodeSchema';

// This performs substrate node name validation, by checking if the node name
// already exists under the same chain being configured.
const Form = withFormik({
  mapPropsToErrors: () => ({
    name: '',
  }),
  mapPropsToValues: () => ({
    name: '',
    node_ws_url: '',
    monitor_ws: false,
    telemetry_url: '',
    monitor_telemetry: false,
    prometheus_url: '',
    monitor_prometheus: false,
    exporter_url: '',
    monitor_system: false,
    stash_address: '',
    is_validator: false,
    monitor_node: true,
    is_archive_node: false,
    use_as_data_source: false,
  }),
  validationSchema: (props) => NodeSchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveNodeDetails, currentChain } = props;
    const payload = {
      parent_id: currentChain,
      name: values.name,
      node_ws_url: values.node_ws_url,
      monitor_ws: values.monitor_ws,
      telemetry_url: values.telemetry_url,
      monitor_telemetry: values.monitor_telemetry,
      prometheus_url: values.prometheus_url,
      monitor_prometheus: values.monitor_prometheus,
      exporter_url: values.exporter_url,
      monitor_system: values.monitor_system,
      stash_address: values.stash_address,
      is_validator: values.is_validator,
      monitor_node: values.monitor_node,
      is_archive_node: values.is_archive_node,
      use_as_data_source: values.use_as_data_source,
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
  chainlinkNodesConfig: state.ChainlinkNodesReducer,
  substrateNodesConfig: state.SubstrateNodesReducer,
  cosmosNodesConfig: state.CosmosNodesReducer,
  reposConfig: state.GitHubRepositoryReducer,
  systemConfig: state.SystemsReducer,
  dockerHubConfig: state.DockerHubReducer,
  evmNodesConfig: state.EvmNodesReducer,
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
const NodesFormContainer = connect(mapStateToProps, mapDispatchToProps)(Form);

// Combine substrate state and dispatch functions to the node table
const NodesTableContainer = connect(
  mapStateToProps,
  mapDispatchToPropsRemove,
)(NodesTable);

export { NodesFormContainer, NodesTableContainer };
