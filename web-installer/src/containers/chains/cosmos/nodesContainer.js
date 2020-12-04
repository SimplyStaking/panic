import { withFormik } from 'formik';
import { connect } from 'react-redux';
import NodesForm from 'components/chains/cosmos/forms/nodesForm';
import NodesTable from 'components/chains/cosmos/tables/nodesTable';
import { addNodeCosmos, removeNodeCosmos } from 'redux/actions/cosmosActions';
import NodeSchema from './schemas/nodeSchema';
import CosmosData from 'data/cosmos';

// This performs cosmos node name validation, by checking if the node name
// already exists under the same chain being configured.
const Form = withFormik({
  mapPropsToErrors: () => ({
    cosmos_node_name: '',
  }),
  mapPropsToValues: () => ({
    cosmos_node_name: '',
    tendermint_rpc_url: '',
    cosmos_rpc_url: '',
    prometheus_url: '',
    exporter_url: '',
    is_validator: false,
    monitor_node: true,
    is_archive_node: true,
    use_as_data_source: true,
  }),
  validationSchema: (props) => NodeSchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveNodeDetails, currentChain } = props;
    const payload = {
      parent_id: currentChain,
      cosmos_node_name: values.cosmos_node_name,
      tendermint_rpc_url: values.tendermint_rpc_url,
      cosmos_rpc_url: values.cosmos_rpc_url,
      prometheus_url: values.prometheus_url,
      exporter_url: values.exporter_url,
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
  nodesConfig: state.CosmosNodesReducer,
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

export {
  NodesFormContainer,
  NodesTableContainer,
};
