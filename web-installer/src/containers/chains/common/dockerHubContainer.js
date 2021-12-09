import { withFormik } from 'formik';
import { connect } from 'react-redux';
import DockerHubForm from 'components/chains/common/forms/dockerHubForm';
import DockerHubTable from 'components/chains/common/tables/dockerHubTable';
import { addDockerHub, removeDockerHub } from 'redux/actions/generalActions';
import { GENERAL } from 'constants/constants';
import GeneralData from 'data/general';
import CosmosData from 'data/cosmos';
import SubstrateData from 'data/substrate';
import ChainlinkData from 'data/chainlink';
import { toggleDirty } from 'redux/actions/pageActions';
import DockerHubSchema from './schemas/dockerHubSchema';

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
  toggleDirtyForm: (tog, { props }) => {
    const { toggleDirtyForm } = props;
    toggleDirtyForm(tog);
  },
  validationSchema: (props) => DockerHubSchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveDockerHubDetails, currentChain } = props;
    const payload = {
      parent_id: currentChain,
      name: values.name,
      monitor_docker: values.monitor_docker,
    };
    saveDockerHubDetails(payload);
    resetForm();
  },
})(DockerHubForm);

// ------------------------- Common Actions --------------------------

// Function to be used by all configuration processes to add dockerHub
// details to the redux state.
function mapDispatchToProps(dispatch) {
  return {
    saveDockerHubDetails: (details) => dispatch(addDockerHub(details)),
    toggleDirtyForm: (tog) => dispatch(toggleDirty(tog)),
  };
}

// Function to be used by all configuration processes to remove dockerHub
// details from the table and state.
function mapDispatchToPropsRemove(dispatch) {
  return {
    removeDockerHubDetails: (details) => dispatch(removeDockerHub(details)),
  };
}

// ------------------------- General Data ----------------------------

// General redux data that will be used to control the repo form and populate
// the dockerHub table.
const mapGeneralStateToProps = (state) => ({
  currentChain: GENERAL,
  config: state.GeneralReducer,
  chainlinkNodesConfig: state.ChainlinkNodesReducer,
  substrateNodesConfig: state.SubstrateNodesReducer,
  cosmosNodesConfig: state.CosmosNodesReducer,
  systemConfig: state.SystemsReducer,
  reposConfig: state.GitHubRepositoryReducer,
  dockerHubConfig: state.DockerHubReducer,
  evmNodesConfig: state.EvmNodesReducer,
  data: GeneralData,
});

// Combine general state and dispatch functions to the dockerHub form
const DockerHubGeneralFormContainer = connect(
  mapGeneralStateToProps,
  mapDispatchToProps,
)(Form);

// Combine general state and dispatch functions to the dockerHub table
const DockerHubGeneralTableContainer = connect(
  mapGeneralStateToProps,
  mapDispatchToPropsRemove,
)(DockerHubTable);

// ------------------------- Cosmos Based Chain Data -----------------

// Cosmos redux data that will be used to control the repo form and populate
// the dockerHub table.
const mapCosmosStateToProps = (state) => ({
  currentChain: state.CurrentCosmosChain,
  config: state.CosmosChainsReducer,
  chainlinkNodesConfig: state.ChainlinkNodesReducer,
  substrateNodesConfig: state.SubstrateNodesReducer,
  cosmosNodesConfig: state.CosmosNodesReducer,
  systemConfig: state.SystemsReducer,
  reposConfig: state.GitHubRepositoryReducer,
  dockerHubConfig: state.DockerHubReducer,
  evmNodesConfig: state.EvmNodesReducer,
  data: CosmosData,
});

// Combine cosmos state and dispatch functions to the dockerHub form
const DockerHubCosmosFormContainer = connect(
  mapCosmosStateToProps,
  mapDispatchToProps,
)(Form);

// Combine cosmos state and dispatch functions to the dockerHub table
const DockerHubCosmosTableContainer = connect(
  mapCosmosStateToProps,
  mapDispatchToPropsRemove,
)(DockerHubTable);

// ------------------------- Chainlink Based Chain Data -----------------

// Chainlink redux data that will be used to control the repo form and populate
// the dockerHub table.
const mapChainlinkStateToProps = (state) => ({
  currentChain: state.CurrentChainlinkChain,
  config: state.ChainlinkChainsReducer,
  substrateNodesConfig: state.SubstrateNodesReducer,
  cosmosNodesConfig: state.CosmosNodesReducer,
  chainlinkNodesConfig: state.ChainlinkNodesReducer,
  systemConfig: state.SystemsReducer,
  reposConfig: state.GitHubRepositoryReducer,
  dockerHubConfig: state.DockerHubReducer,
  evmNodesConfig: state.EvmNodesReducer,
  data: ChainlinkData,
});

// Combine chainlink state and dispatch functions to the dockerHub form
const DockerHubChainlinkFormContainer = connect(
  mapChainlinkStateToProps,
  mapDispatchToProps,
)(Form);

// Combine chainlink state and dispatch functions to the dockerHub table
const DockerHubChainlinkTableContainer = connect(
  mapChainlinkStateToProps,
  mapDispatchToPropsRemove,
)(DockerHubTable);

// ------------------------- Substrate Based Chain Data -----------------

// Substrate redux data that will be used to control the repo form and populate
// the dockerHub table.
const mapSubstrateStateToProps = (state) => ({
  currentChain: state.CurrentSubstrateChain,
  config: state.SubstrateChainsReducer,
  substrateNodesConfig: state.SubstrateNodesReducer,
  cosmosNodesConfig: state.CosmosNodesReducer,
  chainlinkNodesConfig: state.ChainlinkNodesReducer,
  systemConfig: state.SystemsReducer,
  reposConfig: state.GitHubRepositoryReducer,
  dockerHubConfig: state.DockerHubReducer,
  evmNodesConfig: state.EvmNodesReducer,
  data: SubstrateData,
});

// Combine substrate state and dispatch functions to the dockerHub form
const DockerHubSubstrateFormContainer = connect(
  mapSubstrateStateToProps,
  mapDispatchToProps,
)(Form);

// Combine substrate state and dispatch functions to the dockerHub table
const DockerHubSubstrateTableContainer = connect(
  mapSubstrateStateToProps,
  mapDispatchToPropsRemove,
)(DockerHubTable);

export {
  DockerHubGeneralFormContainer,
  DockerHubGeneralTableContainer,
  DockerHubCosmosFormContainer,
  DockerHubCosmosTableContainer,
  DockerHubSubstrateFormContainer,
  DockerHubSubstrateTableContainer,
  DockerHubChainlinkFormContainer,
  DockerHubChainlinkTableContainer,
};
