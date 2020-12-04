import { withFormik } from 'formik';
import { connect } from 'react-redux';
import TelegramForm from 'components/channels/forms/telegramForm';
import TelegramTable from 'components/channels/tables/telegramTable';
import { addTelegram, removeTelegram } from 'redux/actions/channelActions';
import TelegramSchema from './schemas/telegramSchema';

const Form = withFormik({
  mapPropsToErrors: () => ({
    bot_name: '',
    bot_token: '',
    chat_id: '',
  }),
  mapPropsToValues: () => ({
    bot_name: '',
    bot_token: '',
    chat_id: '',
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
      bot_name: values.bot_name,
      bot_token: values.bot_token,
      chat_id: values.chat_id,
      info: values.info,
      warning: values.warning,
      critical: values.critical,
      error: values.error,
      alerts: values.alerts,
      commands: values.commands,
    };
    saveTelegramDetails(payload);
    resetForm();
  },
})(TelegramForm);

const mapStateToProps = (state) => ({
  telegrams: state.TelegramsReducer,
});

function mapDispatchToProps(dispatch) {
  return {
    saveTelegramDetails: (details) => dispatch(addTelegram(details)),
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

export {
  TelegramFormContainer,
  TelegramTableContainer,
};
