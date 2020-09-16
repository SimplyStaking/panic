import { withFormik } from 'formik';
import { connect } from 'react-redux';
import OtherForm from '../../components/other/otherForm';
import updatePeriodic from '../../redux/actions/otherActions';
import OtherSchema from './otherSchema';

const Form = withFormik({
  mapPropsToErrors: () => ({
    periodic: '',
  }),
  mapPropsToValues: () => ({
    periodic: 0,
    enabled: false,
  }),
  validationSchema: () => OtherSchema(),
  handleSubmit: (values, { resetForm, props }) => {
    const { savePeriodicDetails } = props;
    const payload = {
      periodic: values.periodic,
      enabled: values.enabled,
    };
    savePeriodicDetails(payload);
    resetForm();
  },
})(OtherForm);

const mapStateToProps = (state) => ({
  periodic: state.OtherReducer.periodic,
});

function mapDispatchToProps(dispatch) {
  return {
    savePeriodicDetails: (details) => dispatch(updatePeriodic(details)),
  };
}

const OtherFormContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Form);

export default OtherFormContainer;
