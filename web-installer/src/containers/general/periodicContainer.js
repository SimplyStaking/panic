import { withFormik } from 'formik';
import { connect } from 'react-redux';
import PeriodicForm from '../../components/general/form/periodicForm';
import updatePeriodic from '../../redux/actions/generalActions';
import PeriodicSchema from './schemas/periodicSchema';

const Form = withFormik({
  mapPropsToErrors: () => ({
    periodic: '',
  }),
  mapPropsToValues: () => ({
    periodic: 0,
    enabled: false,
  }),
  validationSchema: () => PeriodicSchema(),
  handleSubmit: (values, { resetForm, props }) => {
    const { savePeriodicDetails } = props;
    const payload = {
      periodic: values.periodic,
      enabled: values.enabled,
    };
    savePeriodicDetails(payload);
    resetForm();
  },
})(PeriodicForm);

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
)(Form);

export default PeriodicFormContainer;
