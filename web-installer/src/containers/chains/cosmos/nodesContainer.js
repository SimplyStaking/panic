import { withFormik } from 'formik';
import { connect } from 'react-redux';
import NodesForm from 'components/chains/cosmos/forms/nodesForm';
import NodesTable from 'components/chains/cosmos/tables/nodesTable';
import { addNodeCosmos, removeNodeCosmos, toggleMonitorNetworkNodesCosmos } from 'redux/actions/cosmosActions';
import CosmosData from 'data/cosmos';
import MonitorNetworkNodesForm from 'components/chains/common/forms/monitorNetworkNodesForm';
import { toggleDirty } from 'redux/actions/pageActions';
import NodeSchema from '../common/schemas/nodeSchema';

// This performs cosmos node name validation, by checking if the node name
// already exists under the same chain being configured.
const Form = withFormik({
  mapPropsToErrors: () => ({
    name: '',
  }),
  mapPropsToValues: () => ({
    name: '',
    cosmos_rest_url: '',
    monitor_cosmos_rest: true,
    prometheus_url: '',
    monitor_prometheus: true,
    exporter_url: '',
    monitor_system: true,
    is_validator: true,
    monitor_node: true,
    is_archive_node: true,
    use_as_data_source: true,
    operator_address: '',
    monitor_tendermint_rpc: true,
    tendermint_rpc_url: '',
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
      cosmos_rest_url: values.cosmos_rest_url,
      monitor_cosmos_rest: values.monitor_cosmos_rest,
      prometheus_url: values.prometheus_url,
      monitor_prometheus: values.monitor_prometheus,
      exporter_url: values.exporter_url,
      monitor_system: values.monitor_system,
      is_validator: values.is_validator,
      monitor_node: values.monitor_node,
      is_archive_node: values.is_archive_node,
      use_as_data_source: values.use_as_data_source,
      operator_address: values.operator_address,
      monitor_tendermint_rpc: values.monitor_tendermint_rpc,
      tendermint_rpc_url: values.tendermint_rpc_url,
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

// ------------------------- Cosmos Based Chain Data --------------------

// Cosmos redux data that will be used to control the node form.
const mapStateToProps = (state) => ({
  currentChain: state.CurrentCosmosChain,
  currentChainName: 'cosmos',
  chainConfig: state.CosmosChainsReducer,
  cosmosNodesConfig: state.CosmosNodesReducer,
  substrateNodesConfig: state.SubstrateNodesReducer,
  chainlinkNodesConfig: state.ChainlinkNodesReducer,
  reposConfig: state.GitHubRepositoryReducer,
  systemConfig: state.SystemsReducer,
  dockerHubConfig: state.DockerHubReducer,
  evmNodesConfig: state.EvmNodesReducer,
  data: CosmosData,
});

// Functions to be used in the Cosmos Node form to save the form's details
function mapDispatchToProps(dispatch) {
  return {
    saveNodeDetails: (details) => dispatch(addNodeCosmos(details)),
    toggleDirtyForm: (tog) => dispatch(toggleDirty(tog)),
    toggleMonitorNetworkNodes: (toggle) => dispatch(toggleMonitorNetworkNodesCosmos(toggle)),
  };
}

// Functions to be used in the Cosmos Nodes table to delete the saved details
// from state
function mapDispatchToPropsRemove(dispatch) {
  return {
    removeNodeDetails: (details) => dispatch(removeNodeCosmos(details)),
  };
}

// Combine cosmos state and dispatch functions to the node form
const NodesFormContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Form);

const MonitorNetworkFormContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(MonitorNetworkForm);

// Combine cosmos state and dispatch functions to the node table
const NodesTableContainer = connect(
  mapStateToProps,
  mapDispatchToPropsRemove,
)(NodesTable);

export { NodesFormContainer, MonitorNetworkFormContainer, NodesTableContainer };
