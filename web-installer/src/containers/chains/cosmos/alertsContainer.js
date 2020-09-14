import { connect } from 'react-redux';
import AlertsTable from '../../../components/chains/cosmos/tables/alertsTable';

const mapStateToProps = (state) => ({
  config: state.ChainsReducer.config,
});

// function mapDispatchToProps(dispatch) {
//   return {

//   };
// }

const AlertsTableContainer = connect(
  mapStateToProps,
)(AlertsTable);

export default AlertsTableContainer;
