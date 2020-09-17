import { connect } from 'react-redux';
import PeriodicForm from '../../components/general/forms/periodicForm';
import { updatePeriodic } from '../../redux/actions/generalActions';

const mapStateToProps = (state) => ({
  periodic: state.GeneralReducer.periodic,
});

function mapDispatchToProps(dispatch) {
  return {
    savePeriodicDetails: (details) => dispatch(updatePeriodic(details)),
  };
}

const PeriodicFormContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(PeriodicForm);

export default PeriodicFormContainer;
