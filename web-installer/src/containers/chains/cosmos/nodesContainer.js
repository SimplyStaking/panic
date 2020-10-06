import { withFormik } from 'formik';
import { connect } from 'react-redux';
import NodesForm from '../../../components/chains/cosmos/forms/nodesForm';
import NodesTable from '../../../components/chains/cosmos/tables/nodesTable';
import { addNodeCosmos, removeNodeCosmos } from '../../../redux/actions/cosmosActions';
import NodeSchema from './schemas/nodeSchema';

const Form = withFormik({
  mapPropsToErrors: () => ({
    cosmosNodeName: '',
  }),
  mapPropsToValues: () => ({
    cosmosNodeName: '',
    tendermintRPCURL: '',
    cosmosRPCURL: '',
    prometheusURL: '',
    exporterUrl: '',
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
      cosmosNodeName: values.cosmosNodeName,
      tendermintRPCURL: values.tendermintRPCURL,
      cosmosRPCURL: values.cosmosRPCURL,
      prometheusURL: values.prometheusURL,
      exporterUrl: values.exporterUrl,
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
  currentChain: state.CurrentCosmosChain,
  chainConfig: state.CosmosChainsReducer,
  nodesConfig: state.CosmosNodesReducer,
});

function mapDispatchToProps(dispatch) {
  return {
    saveNodeDetails: (details) => dispatch(addNodeCosmos(details)),
  };
}

function mapDispatchToPropsRemove(dispatch) {
  return {
    removeNodeDetails: (details) => dispatch(removeNodeCosmos(details)),
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
