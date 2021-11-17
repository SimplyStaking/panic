import { withFormik } from 'formik';
import { connect } from 'react-redux';
import NodesForm from 'components/chains/cosmos/forms/nodesForm';
import NodesTable from 'components/chains/cosmos/tables/nodesTable';
import { addNodeCosmos, removeNodeCosmos } from 'redux/actions/cosmosActions';
import CosmosData from 'data/cosmos';
import NodeSchema from '../common/schemas/nodeSchema';

// This performs cosmos node name validation, by checking if the node name
// already exists under the same chain being configured.
const Form = withFormik({
  mapPropsToErrors: () => ({
    name: '',
  }),
  mapPropsToValues: () => ({
    name: '',
    tendermint_rpc_url: '',
    monitor_tendermint: false,
    cosmos_rpc_url: '',
    monitor_rpc: false,
    prometheus_url: '',
    monitor_prometheus: false,
    exporter_url: '',
    monitor_system: true,
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
      tendermint_rpc_url: values.tendermint_rpc_url,
      monitor_tendermint: values.monitor_tendermint,
      cosmos_rpc_url: values.cosmos_rpc_url,
      monitor_rpc: values.monitor_rpc,
      prometheus_url: values.prometheus_url,
      monitor_prometheus: values.monitor_prometheus,
      exporter_url: values.exporter_url,
      monitor_system: values.monitor_system,
      is_validator: values.is_validator,
      monitor_node: values.monitor_node,
      is_archive_node: values.is_archive_node,
      use_as_data_source: values.use_as_data_source,
    };
    saveNodeDetails(payload);
    resetForm();
  },

})(NodesForm);

// ------------------------- Cosmos Based Chain Data --------------------

// Cosmos redux data that will be used to control the node form.
const mapStateToProps = (state) => ({
  currentChain: state.CurrentCosmosChain,
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

// Combine cosmos state and dispatch functions to the node table
const NodesTableContainer = connect(
  mapStateToProps,
  mapDispatchToPropsRemove,
)(NodesTable);

export { NodesFormContainer, NodesTableContainer };
