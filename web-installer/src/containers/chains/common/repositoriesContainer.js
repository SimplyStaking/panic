import { withFormik } from 'formik';
import { connect } from 'react-redux';
import RepositoriesForm from 'components/chains/common/forms/repositoriesForm';
import RepositoriesTable from 'components/chains/common/tables/repositoriesTable';
import { addRepository, removeRepository } from 'redux/actions/generalActions';
import { GENERAL } from 'constants/constants';
import GeneralData from 'data/general';
import CosmosData from 'data/cosmos';
import SubstrateData from 'data/substrate';
import ChainlinkData from 'data/chainlink';
import RepositorySchema from './schemas/repositorySchema';

// This performs repository validation, by checking if the repository is already
// setup.
const Form = withFormik({
  mapPropsToErrors: () => ({
    repo_name: '',
  }),
  mapPropsToValues: () => ({
    repo_name: '',
    monitor_repo: true,
  }),
  validationSchema: (props) => RepositorySchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveRepositoryDetails, currentChain } = props;
    const payload = {
      parent_id: currentChain,
      repo_name: values.repo_name,
      monitor_repo: values.monitor_repo,
    };
    saveRepositoryDetails(payload);
    resetForm();
  },
})(RepositoriesForm);

// ------------------------- Common Actions --------------------------

// Function to be used by all configuration processes to add repository
// details to the redux state.
function mapDispatchToProps(dispatch) {
  return {
    saveRepositoryDetails: (details) => dispatch(addRepository(details)),
  };
}

// Function to be used by all configuration processes to remove repository
// details from the table and state.
function mapDispatchToPropsRemove(dispatch) {
  return {
    removeRepositoryDetails: (details) => dispatch(removeRepository(details)),
  };
}

// ------------------------- General Data ----------------------------

// General redux data that will be used to control the repo form and populate
// the repository table.
const mapGeneralStateToProps = (state) => ({
  currentChain: GENERAL,
  config: state.GeneralReducer,
  chainlinkNodesConfig: state.ChainlinkNodesReducer,
  substrateNodesConfig: state.SubstrateNodesReducer,
  cosmosNodesConfig: state.CosmosNodesReducer,
  systemConfig: state.SystemsReducer,
  reposConfig: state.RepositoryReducer,
  dockerConfig: state.DockerReducer,
  data: GeneralData,
});

// Combine general state and dispatch functions to the repositories form
const RepositoriesGeneralFormContainer = connect(
  mapGeneralStateToProps,
  mapDispatchToProps,
)(Form);

// Combine general state and dispatch functions to the repositories table
const RepositoriesGeneralTableContainer = connect(
  mapGeneralStateToProps,
  mapDispatchToPropsRemove,
)(RepositoriesTable);

// ------------------------- Cosmos Based Chain Data -----------------

// Cosmos redux data that will be used to control the repo form and populate
// the repository table.
const mapCosmosStateToProps = (state) => ({
  currentChain: state.CurrentCosmosChain,
  config: state.CosmosChainsReducer,
  chainlinkNodesConfig: state.ChainlinkNodesReducer,
  substrateNodesConfig: state.SubstrateNodesReducer,
  cosmosNodesConfig: state.CosmosNodesReducer,
  systemConfig: state.SystemsReducer,
  reposConfig: state.RepositoryReducer,
  dockerConfig: state.DockerReducer,
  data: CosmosData,
});

// Combine cosmos state and dispatch functions to the repositories form
const RepositoriesCosmosFormContainer = connect(
  mapCosmosStateToProps,
  mapDispatchToProps,
)(Form);

// Combine cosmos state and dispatch functions to the repositories table
const RepositoriesCosmosTableContainer = connect(
  mapCosmosStateToProps,
  mapDispatchToPropsRemove,
)(RepositoriesTable);

// ------------------------- Chainlink Based Chain Data -----------------

// Chainlink redux data that will be used to control the repo form and populate
// the repository table.
const mapChainlinkStateToProps = (state) => ({
  currentChain: state.CurrentChainlinkChain,
  config: state.ChainlinkChainsReducer,
  chainlinkNodesConfig: state.ChainlinkNodesReducer,
  substrateNodesConfig: state.SubstrateNodesReducer,
  cosmosNodesConfig: state.CosmosNodesReducer,
  systemConfig: state.SystemsReducer,
  reposConfig: state.RepositoryReducer,
  dockerConfig: state.DockerReducer,
  data: ChainlinkData,
});

// Combine chainlink state and dispatch functions to the repositories form
const RepositoriesChainlinkFormContainer = connect(
  mapChainlinkStateToProps,
  mapDispatchToProps,
)(Form);

// Combine chainlink state and dispatch functions to the repositories table
const RepositoriesChainlinkTableContainer = connect(
  mapChainlinkStateToProps,
  mapDispatchToPropsRemove,
)(RepositoriesTable);

// ------------------------- Substrate Based Chain Data -----------------

// Substrate redux data that will be used to control the repo form and populate
// the repository table.
const mapSubstrateStateToProps = (state) => ({
  currentChain: state.CurrentSubstrateChain,
  config: state.SubstrateChainsReducer,
  chainlinkNodesConfig: state.ChainlinkNodesReducer,
  substrateNodesConfig: state.SubstrateNodesReducer,
  cosmosNodesConfig: state.CosmosNodesReducer,
  systemConfig: state.SystemsReducer,
  reposConfig: state.RepositoryReducer,
  dockerConfig: state.DockerReducer,
  data: SubstrateData,
});

// Combine substrate state and dispatch functions to the repositories form
const RepositoriesSubstrateFormContainer = connect(
  mapSubstrateStateToProps,
  mapDispatchToProps,
)(Form);

// Combine substrate state and dispatch functions to the repositories table
const RepositoriesSubstrateTableContainer = connect(
  mapSubstrateStateToProps,
  mapDispatchToPropsRemove,
)(RepositoriesTable);

export {
  RepositoriesGeneralFormContainer,
  RepositoriesGeneralTableContainer,
  RepositoriesCosmosFormContainer,
  RepositoriesCosmosTableContainer,
  RepositoriesSubstrateFormContainer,
  RepositoriesSubstrateTableContainer,
  RepositoriesChainlinkFormContainer,
  RepositoriesChainlinkTableContainer,
};
