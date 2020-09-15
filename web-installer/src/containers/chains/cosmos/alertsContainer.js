import { connect } from 'react-redux';
import {
  updateWarningDelay, updateWarningRepeat, updateWarningThreshold,
  updateWarningTimeWindow, updateWarningEnabled,
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
  };
}

const AlertsTableContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(AlertsTable);

export default AlertsTableContainer;
