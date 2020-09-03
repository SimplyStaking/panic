import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import { Button, Box } from '@material-ui/core';
import { ToastsStore } from 'react-toasts';
import { fetchData, testCall, sendTestEmail } from '../../utils/data';

function SendTestEmailButton({
  disabled, to, smtp, from, user, pass,
}) {
  const onClick = async () => {
    to.forEach(async (emailTo) => {
      try {
        ToastsStore.info(`Sending test e-mail to address ${to}`, 5000);
        await sendTestEmail(smtp, from, emailTo, user, pass);
        ToastsStore.success('Test e-mail sent successfully, check inbox', 5000);
      } catch (e) {
        if (e.response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          ToastsStore.error(
            `Could not send test e-mail. Error: ${e.response.data.error}`, 5000,
          );
        } else {
          // Something happened in setting up the request that triggered an error
          ToastsStore.error(
            `Could not send test e-mail. Error: ${e.message}`, 5000,
          );
        }
      }
    });
  };
  return (
    <Button variant="outlined" size="large" disabled={disabled} onClick={onClick}>
      <Box px={2}>
        Send test e-mail
      </Box>
    </Button>
  );
}

function TestCallButton({
  disabled, twilioPhoneNumbersToDialValid, accountSid, authToken, twilioPhoneNo,
}) {
  const onClick = async () => {
    twilioPhoneNumbersToDialValid.forEach(async (twilioNumber) => {
      try {
        ToastsStore.info(`Calling number ${twilioNumber}`, 5000);
        await testCall(accountSid, authToken, twilioPhoneNo, twilioNumber);
      } catch (e) {
        if (e.response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          ToastsStore.error(
            `Error in calling ${twilioNumber}. Error: ${e.response.data.error
            }`, 5000,
          );
        } else {
          // Something happened in setting up the request that triggered an
          // Error
          ToastsStore.error(
            `Error in calling ${twilioNumber}. Error: ${e.message}`, 5000,
          );
        }
      }
    });
  };
  return (
    <Button variant="outlined" size="large" disabled={disabled} onClick={onClick}>
      <Box px={2}>
        Test call
      </Box>
    </Button>
  );
}

function SendTestAlertButton({ disabled, botChatID, botToken }) {
  const onClick = async () => {
    try {
      ToastsStore.info(
        'Sending test alert. Make sure to check the chat corresponding with '
        + `chat id ${botChatID}`, 5000,
      );
      await fetchData(
        `https://api.telegram.org/bot${botToken}/sendMessage`, {
          chat_id: botChatID,
          text: '*Test Alert*',
          parse_mode: 'Markdown',
        },
      );
      ToastsStore.success('Test alert sent successfully', 5000);
    } catch (e) {
      if (e.response) {
        // The request was made and the server responded with a status code that
        // falls out of the range of 2xx
        ToastsStore.error(
          `Could not send test alert. Error: ${e.response.data.description}`,
          5000,
        );
      } else {
        // Something happened in setting up the request that triggered an Error
        ToastsStore.error(
          `Could not send test alert. Error: ${e.message}`, 5000,
        );
      }
    }
  };
  return (
    <Button variant="outlined" size="large" disabled={disabled} onClick={onClick}>
      <Box px={2}>
        Test
      </Box>
    </Button>
  );
}

SendTestEmailButton.propTypes = forbidExtraProps({
  disabled: PropTypes.bool.isRequired,
  to: PropTypes.arrayOf(PropTypes.string.isRequired).isRequired,
  smtp: PropTypes.string.isRequired,
  from: PropTypes.string.isRequired,
  user: PropTypes.string.isRequired,
  pass: PropTypes.string.isRequired,
});

TestCallButton.propTypes = forbidExtraProps({
  disabled: PropTypes.bool.isRequired,
  accountSid: PropTypes.string.isRequired,
  authToken: PropTypes.string.isRequired,
  twilioPhoneNo: PropTypes.string.isRequired,
  twilioPhoneNumbersToDialValid: PropTypes.arrayOf(
    PropTypes.string.isRequired,
  ).isRequired,
});

SendTestAlertButton.propTypes = forbidExtraProps({
  disabled: PropTypes.bool.isRequired,
  botToken: PropTypes.string.isRequired,
  botChatID: PropTypes.string.isRequired,
});

export {
  SendTestAlertButton, TestCallButton, SendTestEmailButton,
};
