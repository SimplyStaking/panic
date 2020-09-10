import { withFormik } from 'formik';
import { connect } from 'react-redux';
import NodesForm from '../../../components/chains/cosmos/forms/nodesForm';
import NodesTable from '../../../components/chains/cosmos/tables/nodesTable';
import { addNode, removeNode } from '../../../redux/actions/chainsActions';
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
    exporterURL: '',
    isValidator: false,
    monitorNode: true,
    isArchiveNode: true,
    useAsDataSource: true,
  }),
  validationSchema: (props) => NodeSchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveNodeDetails } = props;
    const payload = {
      cosmosNodeName: values.cosmosNodeName,
      tendermintRPCURL: values.tendermintRPCURL,
      cosmosRPCURL: values.cosmosRPCURL,
      prometheusURL: values.prometheusURL,
      exporterURL: values.exporterURL,
      isValidator: values.isValidator,
      monitorNode: values.monitorNode,
      isArchiveNode: values.isArchiveNode,
      useAsDataSource: values.useAsDataSource,
    };
    saveNodeDetails(payload);
    resetForm();
  },
})(NodesForm);

const mapStateToProps = (state) => ({
  cosmosConfigs: state.ChainsReducer.cosmosConfigs,
  config: state.ChainsReducer.config,
});

function mapDispatchToProps(dispatch) {
  return {
    saveNodeDetails: (details) => dispatch(addNode(details)),
  };
}

function mapDispatchToPropsRemove(dispatch) {
  return {
    removeNodeDetails: (details) => dispatch(removeNode(details)),
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
