import { withFormik } from 'formik';
import { connect } from 'react-redux';
import NodesForm from 'components/chains/substrate/forms/nodesForm';
import NodesTable from 'components/chains/substrate/tables/nodesTable';
import {
  addNodeSubstrate,
  removeNodeSubstrate,
  toggleMonitorNetworkNodesSubstrate,
} from 'redux/actions/substrateActions';
import SubstrateData from 'data/substrate';
import { toggleDirty } from 'redux/actions/pageActions';
import MonitorNetworkNodesForm from 'components/chains/common/forms/monitorNetworkNodesForm';
import NodeSchema from '../common/schemas/nodeSchema';

// This performs substrate node name validation, by checking if the node name
// already exists under the same chain being configured.
const Form = withFormik({
  mapPropsToErrors: () => ({
    name: '',
    node_ws_url: '',
    exporter_url: '',
    governance_addresses: '',
    stash_address: '',
  }),
  mapPropsToValues: () => ({
    name: '',
    node_ws_url: '',
    exporter_url: '',
    monitor_system: true,
    governance_addresses: [],
    stash_address: '',
    is_validator: false,
    monitor_node: true,
    is_archive_node: false,
    use_as_data_source: true,
  }),
  toggleDirtyForm: (tog, { props }) => {
    const { toggleDirtyForm } = props;
    toggleDirtyForm(tog);
  },
  validationSchema: (props) => NodeSchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveNodeDetails, currentChain } = props;
    const payload = {
      parent_id: currentChain,
      name: values.name,
      node_ws_url: values.node_ws_url,
      monitor_node: values.monitor_node,
      use_as_data_source: values.use_as_data_source,
      is_validator: values.is_validator,
      is_archive_node: values.is_archive_node,
      exporter_url: values.exporter_url,
      monitor_system: values.monitor_system,
      governance_addresses: values.governance_addresses,
      stash_address: values.stash_address,
      monitor_network: true,
    };
    saveNodeDetails(payload);
    resetForm();
  },
})(NodesForm);

const MonitorNetworkForm = withFormik({
  mapPropsToValues: () => ({
    monitor_network: true,
  }),
  toggleMonitorNetworkNodes: ({ props }) => {
    const { toggleMonitorNetworkNodes, currentChain } = props;
    const payload = {
      parent_id: currentChain,
      monitor_network: props.values.monitor_network,
    };
    toggleMonitorNetworkNodes(payload);
  },
})(MonitorNetworkNodesForm);

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
    toggleDirtyForm: (tog) => dispatch(toggleDirty(tog)),
    toggleMonitorNetworkNodes: (toggle) => dispatch(toggleMonitorNetworkNodesSubstrate(toggle)),
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

const MonitorNetworkFormContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(MonitorNetworkForm);

// Combine substrate state and dispatch functions to the node table
const NodesTableContainer = connect(
  mapStateToProps,
  mapDispatchToPropsRemove,
)(NodesTable);

export { NodesFormContainer, MonitorNetworkFormContainer, NodesTableContainer };
