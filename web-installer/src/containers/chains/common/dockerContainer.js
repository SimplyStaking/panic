import { withFormik } from 'formik';
import { connect } from 'react-redux';
import DockerForm from 'components/chains/common/forms/dockerForm';
import DockerTable from 'components/chains/common/tables/dockerTable';
import { addDocker, removeDocker } from 'redux/actions/generalActions';
import { GENERAL } from 'constants/constants';
import GeneralData from 'data/general';
import CosmosData from 'data/cosmos';
import SubstrateData from 'data/substrate';
import DockerSchema from './schemas/dockerSchema';

// This performs docker validation, by checking if the docker is already
// setup.
const Form = withFormik({
  mapPropsToErrors: () => ({
    name: '',
  }),
  mapPropsToValues: () => ({
    name: '',
    monitor_docker: true,
  }),
  validationSchema: (props) => DockerSchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveDockerDetails, currentChain } = props;
    const payload = {
      parent_id: currentChain,
      name: values.name,
      monitor_docker: values.monitor_docker,
    };
    saveDockerDetails(payload);
    resetForm();
  },
})(DockerForm);

// ------------------------- Common Actions --------------------------

// Function to be used by all configuration processes to add docker
// details to the redux state.
function mapDispatchToProps(dispatch) {
  return {
    saveDockerDetails: (details) => dispatch(addDocker(details)),
  };
}

// Function to be used by all configuration processes to remove docker
// details from the table and state.
function mapDispatchToPropsRemove(dispatch) {
  return {
    removeDockerDetails: (details) => dispatch(removeDocker(details)),
  };
}

// ------------------------- General Data ----------------------------

// General redux data that will be used to control the repo form and populate
// the docker table.
const mapGeneralStateToProps = (state) => ({
  currentChain: GENERAL,
  config: state.GeneralReducer,
  substrateNodesConfig: state.SubstrateNodesReducer,
  cosmosNodesConfig: state.CosmosNodesReducer,
  systemConfig: state.SystemsReducer,
  reposConfig: state.RepositoryReducer,
  dockerConfig: state.DockerReducer,
  data: GeneralData,
});

// Combine general state and dispatch functions to the docker form
const DockerGeneralFormContainer = connect(
  mapGeneralStateToProps,
  mapDispatchToProps,
)(Form);

// Combine general state and dispatch functions to the docker table
const DockerGeneralTableContainer = connect(
  mapGeneralStateToProps,
  mapDispatchToPropsRemove,
)(DockerTable);

// ------------------------- Cosmos Based Chain Data -----------------

// Cosmos redux data that will be used to control the repo form and populate
// the docker table.
const mapCosmosStateToProps = (state) => ({
  currentChain: state.CurrentCosmosChain,
  config: state.CosmosChainsReducer,
  substrateNodesConfig: state.SubstrateNodesReducer,
  cosmosNodesConfig: state.CosmosNodesReducer,
  systemConfig: state.SystemsReducer,
  reposConfig: state.RepositoryReducer,
  dockerConfig: state.DockerReducer,
  data: CosmosData,
});

// Combine cosmos state and dispatch functions to the docker form
const DockerCosmosFormContainer = connect(
  mapCosmosStateToProps,
  mapDispatchToProps,
)(Form);

// Combine cosmos state and dispatch functions to the docker table
const DockerCosmosTableContainer = connect(
  mapCosmosStateToProps,
  mapDispatchToPropsRemove,
)(DockerTable);

// ------------------------- Substrate Based Chain Data -----------------

// Substrate redux data that will be used to control the repo form and populate
// the docker table.
const mapSubstrateStateToProps = (state) => ({
  currentChain: state.CurrentSubstrateChain,
  config: state.SubstrateChainsReducer,
  substrateNodesConfig: state.SubstrateNodesReducer,
  cosmosNodesConfig: state.CosmosNodesReducer,
  systemConfig: state.SystemsReducer,
  reposConfig: state.RepositoryReducer,
  dockerConfig: state.DockerReducer,
  data: SubstrateData,
});

// Combine substrate state and dispatch functions to the docker form
const DockerSubstrateFormContainer = connect(
  mapSubstrateStateToProps,
  mapDispatchToProps,
)(Form);

// Combine substrate state and dispatch functions to the docker table
const DockerSubstrateTableContainer = connect(
  mapSubstrateStateToProps,
  mapDispatchToPropsRemove,
)(DockerTable);

export {
  DockerGeneralFormContainer,
  DockerGeneralTableContainer,
  DockerCosmosFormContainer,
  DockerCosmosTableContainer,
  DockerSubstrateFormContainer,
  DockerSubstrateTableContainer,
};
