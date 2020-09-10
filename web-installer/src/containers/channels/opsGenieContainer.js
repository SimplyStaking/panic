import { withFormik } from 'formik';
import { connect } from 'react-redux';
import OpsGenieForm from '../../components/channels/forms/opsGenie_form';
import OpsGenieTable from '../../components/channels/tables/opsGenie_table';
import { addOpsGenie, removeOpsGenie } from '../../redux/actions/channelActions';
import OpsGenieSchema from './schemas/opsGenieSchema';

const Form = withFormik({
  mapPropsToErrors: () => ({
    configName: '',
    apiToken: '',
  }),
  mapPropsToValues: () => ({
    configName: '',
    apiToken: '',
    info: false,
    warning: false,
    critical: false,
    error: false,
  }),
  validationSchema: (props) => OpsGenieSchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveOpsGenieDetails } = props;
    const payload = {
      configName: values.configName,
      apiToken: values.apiToken,
      info: values.info,
      warning: values.warning,
      critical: values.critical,
      error: values.error,
    };
    saveOpsGenieDetails(payload);
    resetForm();
  },
})(OpsGenieForm);

const mapStateToProps = (state) => ({
  opsGenies: state.ChannelsReducer.opsGenies,
});

function mapDispatchToProps(dispatch) {
  return {
    saveOpsGenieDetails: (details) => dispatch(addOpsGenie(details)),
  };
}

function mapDispatchToPropsRemove(dispatch) {
  return {
    removeOpsGenieDetails: (details) => dispatch(removeOpsGenie(details)),
  };
}

const OpsGenieFormContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Form);

const OpsGenieTableContainer = connect(
  mapStateToProps,
  mapDispatchToPropsRemove,
)(OpsGenieTable);

export {
  OpsGenieFormContainer,
  OpsGenieTableContainer,
};
