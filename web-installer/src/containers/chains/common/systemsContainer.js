import { withFormik } from 'formik';
import { connect } from 'react-redux';
import SystemForm from 'components/chains/common/forms/systemForm';
import SystemTable from 'components/chains/common/tables/systemTable';
import { addSystem, removeSystem } from 'redux/actions/generalActions';
import { changeStep, changePage } from 'redux/actions/pageActions';
import { GENERAL } from 'constants/constants';
import GeneralData from 'data/general';
import ChainlinkData from 'data/chainlink';
import SystemSchema from './schemas/systemSchema';

// Form validation, check if the system name is unique and if the exporter
// URL was provided.
const Form = withFormik({
  mapPropsToErrors: () => ({
    name: '',
    exporter_url: '',
  }),
  mapPropsToValues: () => ({
    name: '',
    exporter_url: '',
    monitor_system: true,
  }),
  validationSchema: (props) => SystemSchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveSystemDetails, currentChain } = props;
    const payload = {
      parent_id: currentChain,
      name: values.name,
      exporter_url: values.exporter_url,
      monitor_system: values.monitor_system,
    };
    saveSystemDetails(payload);
    resetForm();
  },
})(SystemForm);

// ------------------------- Common Actions --------------------------

function mapDispatchToPropsSave(dispatch) {
  return {
    saveSystemDetails: (details) => dispatch(addSystem(details)),
  };
}

function mapDispatchToPropsRemove(dispatch) {
  return {
    removeSystemDetails: (details) => dispatch(removeSystem(details)),
  };
}

// ----------------------------- General State

const mapGeneralStateToProps = (state) => ({
  currentChain: GENERAL,
  config: state.GeneralReducer,
  chainlinkNodesConfig: state.ChainlinkNodesReducer,
  substrateNodesConfig: state.SubstrateNodesReducer,
  cosmosNodesConfig: state.CosmosNodesReducer,
  reposConfig: state.RepositoryReducer,
  dockerConfig: state.DockerReducer,
  systemConfig: state.SystemsReducer,
  data: GeneralData,
});

function mapDispatchToProps(dispatch) {
  return {
    stepChanger: (step) => dispatch(changeStep(step)),
    pageChanger: (page) => dispatch(changePage(page)),
    saveSystemDetails: (details) => dispatch(addSystem(details)),
  };
}

const SystemGeneralFormContainer = connect(
  mapGeneralStateToProps,
  mapDispatchToProps,
)(Form);

const SystemGeneralTableContainer = connect(
  mapGeneralStateToProps,
  mapDispatchToPropsRemove,
)(SystemTable);

// ----------------------------- Chainlink State

const mapChainlinkStateToProps = (state) => ({
  currentChain: state.CurrentChainlinkChain,
  config: state.ChainlinkChainsReducer,
  substrateNodesConfig: state.SubstrateNodesReducer,
  chainlinkNodesConfig: state.ChainlinkNodesReducer,
  cosmosNodesConfig: state.CosmosNodesReducer,
  reposConfig: state.RepositoryReducer,
  dockerConfig: state.DockerReducer,
  systemConfig: state.SystemsReducer,
  data: ChainlinkData,
});

const SystemChainlinkFormContainer = connect(
  mapChainlinkStateToProps,
  mapDispatchToPropsSave,
)(Form);

const SystemChainlinkTableContainer = connect(
  mapChainlinkStateToProps,
  mapDispatchToPropsRemove,
)(SystemTable);

export {
  SystemGeneralFormContainer, SystemGeneralTableContainer,
  SystemChainlinkFormContainer, SystemChainlinkTableContainer,
};
