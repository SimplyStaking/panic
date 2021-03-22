import { withFormik } from 'formik';
import { connect } from 'react-redux';
import PeriodicForm from 'components/general/forms/periodicForm';
import { updatePeriodic } from 'redux/actions/generalActions';

const Form = withFormik({
  mapPropsToValues: (props) => ({
    time: props.periodic.time,
    enabled: props.periodic.enabled,
  }),
})(PeriodicForm);

const mapStateToProps = (state) => ({
  periodic: state.PeriodicReducer,
});

function mapDispatchToProps(dispatch) {
  return {
    savePeriodicDetails: (details) => dispatch(updatePeriodic(details)),
  };
}

const PeriodicFormContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Form);

export default PeriodicFormContainer;
