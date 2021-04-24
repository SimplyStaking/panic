import { withFormik } from 'formik';
import { connect } from 'react-redux';
import SlackForm from 'components/channels/forms/slackForm';
import SlackTable from 'components/channels/tables/slackTable';
import { addSlack, removeSlack } from 'redux/actions/channelActions';
import TelegramSchema from './schemas/telegramSchema';

const Form = withFormik({
  mapPropsToErrors: () => ({
    channel_name: '',
    chat_id: '',
    token: '',
  }),
  mapPropsToValues: () => ({
    channel_name: '',
    chat_id: '',
    token: '',
    info: false,
    warning: false,
    critical: false,
    error: false,
    alerts: true,
    commands: true,
  }),
  validationSchema: (props) => TelegramSchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveTelegramDetails } = props;
    const payload = {
      channel_name: values.channel_name,
      token: values.token,
      chat_id: values.chat_id,
      info: values.info,
      warning: values.warning,
      critical: values.critical,
      error: values.error,
      alerts: values.alerts,
      commands: values.commands,
      parent_ids: [],
      parent_names: [],
    };
    saveTelegramDetails(payload);
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
