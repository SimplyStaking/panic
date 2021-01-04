import { connect } from 'react-redux';
import {
  updateRepeatAlert,
  updateTimeWindowAlert,
  updateThresholdAlert,
  updateSeverityAlert,
} from 'redux/actions/alertActions';
import { resetCurrentChainIdCosmos } from 'redux/actions/cosmosActions';
import { resetCurrentChainIdSubstrate } from 'redux/actions/substrateActions';
import { changePage, changeStep } from 'redux/actions/pageActions';
import AlertsTable from 'components/chains/common/tables/alertsTable';
import GeneralAlertsTable from 'components/chains/common/tables/generalAlertsTable';
import { GLOBAL } from 'constants/constants';
import CosmosData from 'data/cosmos';
import SubstrateData from 'data/substrate';
import GeneralData from 'data/general';

// ------------------------- Cosmos Based Chain Data --------------------

// Cosmos redux data that will be used to control the alerts table.
const mapCosmosStateToProps = (state) => ({
  currentChain: state.CurrentCosmosChain,
  config: state.CosmosChainsReducer,
  data: CosmosData,
});

// Functions to be used in the Cosmos Alerts table to save the alert's details
function mapCosmosDispatchToProps(dispatch) {
  return {
    stepChanger: (step) => dispatch(changeStep(step)),
    pageChanger: (page) => dispatch(changePage(page)),
    clearChainId: () => dispatch(resetCurrentChainIdCosmos()),
    updateRepeatAlertDetails: (details) => dispatch(updateRepeatAlert(details)),
    updateTimeWindowAlertDetails: (details) => dispatch(updateTimeWindowAlert(details)),
    updateThresholdAlertDetails: (details) => dispatch(updateThresholdAlert(details)),
    updateSeverityAlertDetails: (details) => dispatch(updateSeverityAlert(details)),
  };
}

// Combine cosmos state and dispatch functions to the alerts table
const AlertsCosmosTableContainer = connect(
  mapCosmosStateToProps,
  mapCosmosDispatchToProps,
)(AlertsTable);

// ------------------------- Substrate Based Chain Data --------------------

// Substrate redux data that will be used to control the alerts table.
const mapSubstrateStateToProps = (state) => ({
  currentChain: state.CurrentSubstrateChain,
  config: state.SubstrateChainsReducer,
  data: SubstrateData,
});

// Functions to be used in the Substrate Alerts table to save the alert's
// details
function mapSubstrateDispatchToProps(dispatch) {
  return {
    stepChanger: (step) => dispatch(changeStep(step)),
    pageChanger: (page) => dispatch(changePage(page)),
    clearChainId: () => dispatch(resetCurrentChainIdSubstrate()),
    updateRepeatAlertDetails: (details) => dispatch(updateRepeatAlert(details)),
    updateTimeWindowAlertDetails: (details) => dispatch(updateTimeWindowAlert(details)),
    updateThresholdAlertDetails: (details) => dispatch(updateThresholdAlert(details)),
    updateSeverityAlertDetails: (details) => dispatch(updateSeverityAlert(details)),
  };
}

// Combine general state and dispatch functions to the alerts table
const AlertsSubstrateTableContainer = connect(
  mapSubstrateStateToProps,
  mapSubstrateDispatchToProps,
)(AlertsTable);

// ------------------------- General Data -----------------------------

// General redux data that will be used to control the alerts table.
const mapGeneralStateToProps = (state) => ({
  currentChain: GLOBAL,
  config: state.GeneralReducer,
  data: GeneralData,
});

// Functions to be used in the General Alerts table to save the alert's
// details
function mapGeneralDispatchToProps(dispatch) {
  return {
    stepChanger: (step) => dispatch(changeStep(step)),
    pageChanger: (page) => dispatch(changePage(page)),
    clearChainId: () => dispatch(resetCurrentChainIdSubstrate()),
    updateThresholdAlertDetails: (details) => dispatch(updateThresholdAlert(details)),
    updateRepeatAlertDetails: (details) => dispatch(updateRepeatAlert(details)),
  };
}

// Combine general state and dispatch functions to the alerts table
const AlertsGeneralTableContainer = connect(
  mapGeneralStateToProps,
  mapGeneralDispatchToProps,
)(GeneralAlertsTable);

export {
  AlertsCosmosTableContainer,
  AlertsSubstrateTableContainer,
  AlertsGeneralTableContainer,
};
