import { withFormik } from 'formik';
import { connect } from 'react-redux';
import TelegramForm from '../../components/channels/forms/telegram_form';
import { addTelegram } from '../../redux/actions/channelActions';
import TelegramSchema from './schemas/telegramSchema';

const TelegramContainer = withFormik({
  mapPropsToErrors: () => ({
    botName: '',
    botToken: '',
    chatID: '',
  }),
  mapPropsToValues: () => ({
    botName: '',
    botToken: '',
    chatID: '',
    info: false,
    warning: false,
    critical: false,
    error: false,
    alerts: true,
    commands: true,
    enabled: true,
  }),
  validationSchema: (props) => TelegramSchema(props),
  handleSubmit: (values, { resetForm, props }) => {
    const { saveTelegramDetails } = props;
    const payload = {
      botName: values.botName,
      botToken: values.botToken,
      chatID: values.chatID,
      info: values.info,
      warning: values.warning,
      critical: values.critical,
      error: values.error,
      alerts: values.alerts,
      commands: values.commands,
      enabled: values.enabled,
    };
    saveTelegramDetails(payload);
    resetForm();
  },
})(TelegramForm);

const mapStateToProps = (state) => ({
  telegrams: state.ChannelsReducer.telegrams,
});

function mapDispatchToProps(dispatch) {
  return {
    saveTelegramDetails: (details) => dispatch(addTelegram(details)),
  };
}

export default connect(mapStateToProps, mapDispatchToProps)(TelegramContainer);
