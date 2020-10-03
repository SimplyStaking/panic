import { connect } from 'react-redux';
import { updateThresholdAlert } from '../../../redux/actions/generalActions';
import { changePage, changeStep } from '../../../redux/actions/pageActions';
import AlertsTable from '../../../components/chains/general/tables/alertsTable';

const mapStateToProps = (state) => ({
  generalConfig: state.GeneralReducer,
});

function mapDispatchToProps(dispatch) {
  return {
    stepChanger: (step) => dispatch(changeStep(step)),
    pageChanger: (page) => dispatch(changePage(page)),
    updateThresholdAlertDetails: (details) => dispatch(updateThresholdAlert(details)),
  };
}

const AlertsTableContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(AlertsTable);

export default AlertsTableContainer;
