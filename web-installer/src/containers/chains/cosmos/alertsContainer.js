import { connect } from 'react-redux';
import {
  updateRepeatAlert, updateTimeWindowAlert, updateThresholdAlert,
  updateSeverityAlert,
} from '../../../redux/actions/alertActions';
import { resetCurrentChainIdCosmos } from '../../../redux/actions/cosmosActions';
import { changePage, changeStep } from '../../../redux/actions/pageActions';
import AlertsTable from '../../../components/chains/cosmos/tables/alertsTable';

const mapStateToProps = (state) => ({
  currentChain: state.CurrentCosmosChain,
  chainConfig: state.CosmosChainsReducer,
});

function mapDispatchToProps(dispatch) {
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

const AlertsTableContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(AlertsTable);

export default AlertsTableContainer;
