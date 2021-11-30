import { withFormik } from 'formik';
import { connect } from 'react-redux';
import TelegramForm from 'components/channels/forms/telegramForm';
import TelegramTable from 'components/channels/tables/telegramTable';
import { addTelegram, removeTelegram } from 'redux/actions/channelActions';
import { toggleDirty } from 'redux/actions/pageActions';
import TelegramSchema from './schemas/telegramSchema';

const Form = withFormik({
  mapPropsToErrors: () => ({
    channel_name: '',
    bot_token: '',
    chat_id: '',
  }),
  mapPropsToValues: () => ({
    channel_name: '',
    bot_token: '',
    chat_id: '',
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
  validationSchema: (props) => TelegramSchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveTelegramDetails } = props;
    const payload = {
      channel_name: values.channel_name,
      bot_token: values.bot_token,
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
})(TelegramForm);

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
    saveTelegramDetails: (details) => dispatch(addTelegram(details)),
    toggleDirtyForm: (tog) => dispatch(toggleDirty(tog)),
  };
}

function mapDispatchToPropsRemove(dispatch) {
  return {
    removeTelegramDetails: (details) => dispatch(removeTelegram(details)),
  };
}

const TelegramFormContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Form);

const TelegramTableContainer = connect(
  mapStateToProps,
  mapDispatchToPropsRemove,
)(TelegramTable);

export { TelegramFormContainer, TelegramTableContainer };
