import { connect } from 'react-redux';
import {
  updateWarningDelay, updateWarningRepeat, updateWarningThreshold,
  updateWarningTimeWindow, updateWarningEnabled, updateCriticalDelay,
  updateCriticalRepeat, updateCriticalThreshold, updateCriticalTimeWindow,
  updateCriticalEnabled, updateAlertEnabled, updateAlertSeverityLevel,
  updateAlertSeverityEnabled,
} from '../../../redux/actions/chainsActions';
import AlertsTable from '../../../components/chains/cosmos/tables/alertsTable';

const mapStateToProps = (state) => ({
  config: state.ChainsReducer.config,
});

function mapDispatchToProps(dispatch) {
  return {
    updateWarningDelay: (details) => dispatch(updateWarningDelay(details)),
    updateWarningRepeat: (details) => dispatch(updateWarningRepeat(details)),
    updateWarningThreshold: (details) => dispatch(updateWarningThreshold(details)),
    updateWarningTimeWindow: (details) => dispatch(updateWarningTimeWindow(details)),
    updateWarningEnabled: (details) => dispatch(updateWarningEnabled(details)),
    updateCriticalDelay: (details) => dispatch(updateCriticalDelay(details)),
    updateCriticalRepeat: (details) => dispatch(updateCriticalRepeat(details)),
    updateCriticalThreshold: (details) => dispatch(updateCriticalThreshold(details)),
    updateCriticalTimeWindow: (details) => dispatch(updateCriticalTimeWindow(details)),
    updateCriticalEnabled: (details) => dispatch(updateCriticalEnabled(details)),
    updateAlertEnabled: (details) => dispatch(updateAlertEnabled(details)),
    updateAlertSeverityLevel: (details) => dispatch(updateAlertSeverityLevel(details)),
    updateAlertSeverityEnabled: (details) => dispatch(updateAlertSeverityEnabled(details)),
  };
}

const AlertsTableContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(AlertsTable);

export default AlertsTableContainer;
