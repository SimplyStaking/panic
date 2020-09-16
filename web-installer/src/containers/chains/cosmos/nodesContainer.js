import { withFormik } from 'formik';
import { connect } from 'react-redux';
import NodesForm from '../../../components/chains/cosmos/forms/nodesForm';
import NodesTable from '../../../components/chains/cosmos/tables/nodesTable';
import { addNodeCosmos, removeNodeCosmos } from '../../../redux/actions/cosmosChainsActions';
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
  cosmosConfigs: state.CosmosChainsReducer.cosmosConfigs,
  config: state.CosmosChainsReducer.config,
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
