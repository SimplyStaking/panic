import { withFormik } from 'formik';
import { connect } from 'react-redux';
import NodesForm from 'components/chains/chainlink/forms/nodesForm';
import NodesTable from 'components/chains/chainlink/tables/nodesTable';
import { addNodeChainlink, removeNodeChainlink } from 'redux/actions/chainlinkActions';
import ChainlinkData from 'data/chainlink';
import ChainlinkNodeSchema from './chainlinkNodeSchema';

// This performs chainlink node name validation, by checking if the node name
// already exists under the same chain being configured.
const Form = withFormik({
  mapPropsToErrors: () => ({
    name: '',
  }),
  mapPropsToValues: () => ({
    name: '',
    node_prometheus_urls: [],
    monitor_prometheus: true,
    monitor_node: true,
  }),
  validationSchema: (props) => ChainlinkNodeSchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveNodeDetails, currentChain } = props;
    const payload = {
      parent_id: currentChain,
      name: values.name,
      node_prometheus_urls: values.node_prometheus_urls,
      monitor_prometheus: values.monitor_prometheus,
      monitor_node: values.monitor_node,
    };
    saveNodeDetails(payload);
    resetForm();
  },
})(NodesForm);

// ------------------------- Chainlink Based Chain Data --------------------

// Chainlink redux data that will be used to control the node form.
const mapStateToProps = (state) => ({
  currentChain: state.CurrentChainlinkChain,
  chainConfig: state.ChainlinkChainsReducer,
  chainlinkNodesConfig: state.ChainlinkNodesReducer,
  cosmosNodesConfig: state.CosmosNodesReducer,
  substrateNodesConfig: state.SubstrateNodesReducer,
  reposConfig: state.GitHubRepositoryReducer,
  systemConfig: state.SystemsReducer,
  dockerHubConfig: state.DockerHubReducer,
  data: ChainlinkData,
});

// Functions to be used in the Chainlink Node form to save the form's details
function mapDispatchToProps(dispatch) {
  return {
    saveNodeDetails: (details) => dispatch(addNodeChainlink(details)),
  };
}

// Functions to be used in the Chainlink Nodes table to delete the saved details
// from state
function mapDispatchToPropsRemove(dispatch) {
  return {
    removeNodeDetails: (details) => dispatch(removeNodeChainlink(details)),
  };
}

// Combine chainlink state and dispatch functions to the node form
const NodesFormContainer = connect(mapStateToProps, mapDispatchToProps)(Form);

// Combine chainlink state and dispatch functions to the node table
const NodesTableContainer = connect(
  mapStateToProps,
  mapDispatchToPropsRemove,
)(NodesTable);

export { NodesFormContainer, NodesTableContainer };
