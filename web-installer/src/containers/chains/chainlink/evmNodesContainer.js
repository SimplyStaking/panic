import { withFormik } from 'formik';
import { connect } from 'react-redux';
import EvmNodesForm from 'components/chains/chainlink/forms/evmNodesForm';
import EvmNodesTable from 'components/chains/chainlink/tables/evmNodesTable';
import { addNodeEvm, removeNodeEvm } from 'redux/actions/chainlinkActions';
import ChainlinkData from 'data/chainlink';
import EvmNodeSchema from './schemas/evmNodeSchema';

// This performs evm node name validation, by checking if the node name
// already exists under the same chain being configured.
const Form = withFormik({
  mapPropsToErrors: () => ({
    name: '',
  }),
  mapPropsToValues: () => ({
    name: '',
    node_http_url: '',
    monitor_node: true,
  }),
  validationSchema: (props) => EvmNodeSchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveNodeDetails, currentChain } = props;
    const payload = {
      parent_id: currentChain,
      name: values.name,
      node_http_url: values.node_http_url,
      monitor_node: values.monitor_node,
    };
    saveNodeDetails(payload);
    resetForm();
  },
})(EvmNodesForm);

// ------------------------- EVM Node Based Chain Data --------------------

// EVM redux data that will be used to control the node form.
const mapStateToProps = (state) => ({
  currentChain: state.CurrentChainlinkChain,
  chainConfig: state.ChainlinkChainsReducer,
  chainlinkNodesConfig: state.ChainlinkNodesReducer,
  cosmosNodesConfig: state.CosmosNodesReducer,
  substrateNodesConfig: state.SubstrateNodesReducer,
  reposConfig: state.GitHubRepositoryReducer,
  systemConfig: state.SystemsReducer,
  dockerHubConfig: state.DockerHubReducer,
  evmNodesConfig: state.EvmNodesReducer,
  data: ChainlinkData,
});

// Functions to be used in the EVM Node form to save the form's details
function mapDispatchToProps(dispatch) {
  return {
    saveNodeDetails: (details) => dispatch(addNodeEvm(details)),
  };
}

// Functions to be used in the EVM Nodes table to delete the saved details
// from state
function mapDispatchToPropsRemove(dispatch) {
  return {
    removeNodeDetails: (details) => dispatch(removeNodeEvm(details)),
  };
}

// Combine evm state and dispatch functions to the node form
const EvmNodesFormContainer = connect(mapStateToProps, mapDispatchToProps)(Form);

// Combine chainlink state and dispatch functions to the node table
const EvmNodesTableContainer = connect(
  mapStateToProps,
  mapDispatchToPropsRemove,
)(EvmNodesTable);

export { EvmNodesFormContainer, EvmNodesTableContainer };
