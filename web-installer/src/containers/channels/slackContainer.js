import { withFormik } from 'formik';
import { connect } from 'react-redux';
import SlackForm from 'components/channels/forms/slackForm';
import SlackTable from 'components/channels/tables/slackTable';
import { addSlack, removeSlack } from 'redux/actions/channelActions';
import { toggleDirty } from 'redux/actions/pageActions';
import SlackSchema from './schemas/slackSchema';

const Form = withFormik({
  mapPropsToErrors: () => ({
    channel_name: '',
    bot_token: '',
    app_token: '',
    bot_channel_id: '',
  }),
  mapPropsToValues: () => ({
    channel_name: '',
    bot_token: '',
    app_token: '',
    bot_channel_id: '',
    info: false,
    warning: false,
    critical: false,
    error: false,
    alerts: true,
    commands: true,
  }),
  toggleDirtyForm: (tog, { props }) => {
    const { toggleDirtyForm } = props;
    toggleDirtyForm(tog);
  },
  validationSchema: (props) => SlackSchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveSlackDetails } = props;
    const payload = {
      channel_name: values.channel_name,
      bot_token: values.bot_token,
      app_token: values.app_token,
      bot_channel_id: values.bot_channel_id,
      info: values.info,
      warning: values.warning,
      critical: values.critical,
      error: values.error,
      alerts: values.alerts,
      commands: values.commands,
      parent_ids: [],
      parent_names: [],
    };
    saveSlackDetails(payload);
    resetForm();
  },
})(SlackForm);

const mapStateToProps = (state) => ({
  emails: state.EmailsReducer,
  opsGenies: state.OpsGenieReducer,
  pagerDuties: state.PagerDutyReducer,
  telegrams: state.TelegramsReducer,
  twilios: state.TwiliosReducer,
  slacks: state.SlacksReducer,
});

function mapDispatchToProps(dispatch) {
  return {
    saveSlackDetails: (details) => dispatch(addSlack(details)),
    toggleDirtyForm: (tog) => dispatch(toggleDirty(tog)),
  };
}

function mapDispatchToPropsRemove(dispatch) {
  return {
    removeSlackDetails: (details) => dispatch(removeSlack(details)),
  };
}

const SlackFormContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Form);

const SlackTableContainer = connect(
  mapStateToProps,
  mapDispatchToPropsRemove,
)(SlackTable);

export { SlackFormContainer, SlackTableContainer };
