import { connect } from 'react-redux';
import {
  updateWarningDelayCosmos, updateWarningRepeatCosmos, updateWarningThresholdCosmos,
  updateWarningTimeWindowCosmos, updateWarningEnabledCosmos, updateCriticalDelayCosmos,
  updateCriticalRepeatCosmos, updateCriticalThresholdCosmos, updateCriticalTimeWindowCosmos,
  updateCriticalEnabledCosmos, updateAlertEnabledCosmos, updateAlertSeverityLevelCosmos,
  updateAlertSeverityEnabledCosmos, addConfigCosmos, resetConfigCosmos,
} from '../../../redux/actions/cosmosChainsActions';
import { changePage, changeStep } from '../../../redux/actions/pageActions';
import AlertsTable from '../../../components/chains/cosmos/tables/alertsTable';

const mapStateToProps = (state) => ({
  config: state.CosmosChainsReducer.config,
});

function mapDispatchToProps(dispatch) {
  return {
    stepChanger: (step) => dispatch(changeStep(step)),
    pageChanger: (page) => dispatch(changePage(page)),
    addConfiguration: () => dispatch(addConfigCosmos()),
    resetConfiguration: () => dispatch(resetConfigCosmos()),
    updateWarningDelayCosmos:
      (details) => dispatch(updateWarningDelayCosmos(details)),
    updateWarningRepeatCosmos:
      (details) => dispatch(updateWarningRepeatCosmos(details)),
    updateWarningThresholdCosmos:
      (details) => dispatch(updateWarningThresholdCosmos(details)),
    updateWarningTimeWindowCosmos:
      (details) => dispatch(updateWarningTimeWindowCosmos(details)),
    updateWarningEnabledCosmos:
      (details) => dispatch(updateWarningEnabledCosmos(details)),
    updateCriticalDelayCosmos:
      (details) => dispatch(updateCriticalDelayCosmos(details)),
    updateCriticalRepeatCosmos:
      (details) => dispatch(updateCriticalRepeatCosmos(details)),
    updateCriticalThresholdCosmos:
      (details) => dispatch(updateCriticalThresholdCosmos(details)),
    updateCriticalTimeWindowCosmos:
      (details) => dispatch(updateCriticalTimeWindowCosmos(details)),
    updateCriticalEnabledCosmos:
      (details) => dispatch(updateCriticalEnabledCosmos(details)),
    updateAlertEnabledCosmos:
      (details) => dispatch(updateAlertEnabledCosmos(details)),
    updateAlertSeverityLevelCosmos:
      (details) => dispatch(updateAlertSeverityLevelCosmos(details)),
    updateAlertSeverityEnabledCosmos:
      (details) => dispatch(updateAlertSeverityEnabledCosmos(details)),
  };
}

const AlertsTableContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(AlertsTable);

export default AlertsTableContainer;
