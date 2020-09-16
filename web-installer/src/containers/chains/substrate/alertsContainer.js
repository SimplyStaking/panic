import { connect } from 'react-redux';
import {
  updateWarningDelaySubstrate, updateWarningRepeatSubstrate,
  updateWarningThresholdSubstrate, updateWarningTimeWindowSubstrate,
  updateWarningEnabledSubstrate, updateCriticalDelaySubstrate,
  updateCriticalRepeatSubstrate, updateCriticalThresholdSubstrate,
  updateCriticalTimeWindowSubstrate, updateCriticalEnabledSubstrate,
  updateAlertEnabledSubstrate, updateAlertSeverityLevelSubstrate,
  updateAlertSeverityEnabledSubstrate, addConfigSubstrate, resetConfigSubstrate,
} from '../../../redux/actions/substrateChainsActions';
import { changePage, changeStep } from '../../../redux/actions/pageActions';
import AlertsTable from '../../../components/chains/substrate/tables/alertsTable';

const mapStateToProps = (state) => ({
  config: state.SubstrateChainsReducer.config,
});

function mapDispatchToProps(dispatch) {
  return {
    stepChanger: (step) => dispatch(changeStep(step)),
    pageChanger: (page) => dispatch(changePage(page)),
    addConfiguration: () => dispatch(addConfigSubstrate()),
    resetConfiguration: () => dispatch(resetConfigSubstrate()),
    updateWarningDelaySubstrate:
      (details) => dispatch(updateWarningDelaySubstrate(details)),
    updateWarningRepeatSubstrate:
      (details) => dispatch(updateWarningRepeatSubstrate(details)),
    updateWarningThresholdSubstrate:
      (details) => dispatch(updateWarningThresholdSubstrate(details)),
    updateWarningTimeWindowSubstrate:
      (details) => dispatch(updateWarningTimeWindowSubstrate(details)),
    updateWarningEnabledSubstrate:
      (details) => dispatch(updateWarningEnabledSubstrate(details)),
    updateCriticalDelaySubstrate:
      (details) => dispatch(updateCriticalDelaySubstrate(details)),
    updateCriticalRepeatSubstrate:
      (details) => dispatch(updateCriticalRepeatSubstrate(details)),
    updateCriticalThresholdSubstrate:
      (details) => dispatch(updateCriticalThresholdSubstrate(details)),
    updateCriticalTimeWindowSubstrate:
      (details) => dispatch(updateCriticalTimeWindowSubstrate(details)),
    updateCriticalEnabledSubstrate:
      (details) => dispatch(updateCriticalEnabledSubstrate(details)),
    updateAlertEnabledSubstrate:
      (details) => dispatch(updateAlertEnabledSubstrate(details)),
    updateAlertSeverityLevelSubstrate:
      (details) => dispatch(updateAlertSeverityLevelSubstrate(details)),
    updateAlertSeverityEnabledSubstrate:
      (details) => dispatch(updateAlertSeverityEnabledSubstrate(details)),
  };
}

const AlertsTableContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(AlertsTable);

export default AlertsTableContainer;
