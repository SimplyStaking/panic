import { withFormik } from 'formik';
import { connect } from 'react-redux';
import ChainForm from 'components/chains/common/forms/chainForm';
import {
  addChainCosmos,
  updateChainCosmos,
  resetCurrentChainIdCosmos,
} from 'redux/actions/cosmosActions';
import {
  addChainChainlink,
  updateChainChainlink,
  resetCurrentChainIdChainlink,
} from 'redux/actions/chainlinkActions';
import {
  addChainSubstrate,
  updateChainSubstrate,
  resetCurrentChainIdSubstrate,
} from 'redux/actions/substrateActions';
import { changeStep, changePage } from 'redux/actions/pageActions';
import CosmosData from 'data/cosmos';
import SubstrateData from 'data/substrate';
import ChainlinkData from 'data/chainlink';
import ChainSchema from './schemas/chainSchema';

// This performs chain name validation, by checking if the base chain already
// has a chain configured under the same name.
const Form = withFormik({
  mapPropsToErrors: () => ({
    chain_name: '',
  }),
  // If the current chain is set then load the name of that chain otherwise
  // return the blank output for the chain name form.
  mapPropsToValues: (props) => ({
    chain_name: props.currentChain
      ? props.config.byId[props.currentChain].chain_name
      : props.currentChain,
  }),
  validationSchema: (props) => ChainSchema(props),
  validateOnMount: true,
})(ChainForm);

// ------------------------- Cosmos Based Chain Data --------------------

// Cosmos redux data that will be used to control the chain form.
const mapCosmosStateToProps = (state) => ({
  step: state.ChangeStepReducer.step,
  config: state.CosmosChainsReducer,
  config2: state.ChainlinkChainsReducer,
  config3: state.SubstrateChainsReducer,
  currentChain: state.CurrentCosmosChain,
  data: CosmosData,
});

// Functions to be used in the Cosmos Chain Form
function mapCosmosDispatchToProps(dispatch) {
  return {
    saveChainDetails: (details) => dispatch(addChainCosmos(details)),
    updateChainDetails: (details) => dispatch(updateChainCosmos(details)),
    clearChainId: () => dispatch(resetCurrentChainIdCosmos()),
    stepChanger: (step) => dispatch(changeStep(step)),
    pageChanger: (page) => dispatch(changePage(page)),
  };
}

// Combine cosmos state and dispatch functions to the chains form
const CosmosChainFormContainer = connect(
  mapCosmosStateToProps,
  mapCosmosDispatchToProps,
)(Form);

// ------------------------- Chainlink Based Chain Data --------------------

// Chainlink redux data that will be used to control the chain form.
const mapChainlinkStateToProps = (state) => ({
  step: state.ChangeStepReducer.step,
  config: state.ChainlinkChainsReducer,
  config2: state.CosmosChainsReducer,
  config3: state.SubstrateChainsReducer,
  currentChain: state.CurrentChainlinkChain,
  data: ChainlinkData,
});

// Functions to be used in the Cosmos Chain Form
function mapChainlinkDispatchToProps(dispatch) {
  return {
    saveChainDetails: (details) => dispatch(addChainChainlink(details)),
    updateChainDetails: (details) => dispatch(updateChainChainlink(details)),
    clearChainId: () => dispatch(resetCurrentChainIdChainlink()),
    stepChanger: (step) => dispatch(changeStep(step)),
    pageChanger: (page) => dispatch(changePage(page)),
  };
}

// Combine chainlink state and dispatch functions to the chains form
const ChainlinkChainFormContainer = connect(
  mapChainlinkStateToProps,
  mapChainlinkDispatchToProps,
)(Form);

// ------------------------- Substrate Based Chain Data --------------------

// Substrate redux data that will be used to control the chain form.
const mapSubstrateStateToProps = (state) => ({
  step: state.ChangeStepReducer.step,
  config: state.SubstrateChainsReducer,
  config2: state.CosmosChainsReducer,
  config3: state.ChainlinkChainsReducer,
  currentChain: state.CurrentSubstrateChain,
  data: SubstrateData,
});

// Functions to be used in the Substrate Chain Form
function mapSubstrateDispatchToProps(dispatch) {
  return {
    saveChainDetails: (details) => dispatch(addChainSubstrate(details)),
    updateChainDetails: (details) => dispatch(updateChainSubstrate(details)),
    clearChainId: () => dispatch(resetCurrentChainIdSubstrate()),
    stepChanger: (step) => dispatch(changeStep(step)),
    pageChanger: (page) => dispatch(changePage(page)),
  };
}

// Combine substrate state and dispatch functions to the chains form
const SubstrateChainFormContainer = connect(
  mapSubstrateStateToProps,
  mapSubstrateDispatchToProps,
)(Form);

export {
  CosmosChainFormContainer,
  SubstrateChainFormContainer,
  ChainlinkChainFormContainer,
};
