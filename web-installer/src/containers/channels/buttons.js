import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import { Button, Box } from '@material-ui/core';
import { ToastsStore } from 'react-toasts';
import { fetchData, testCall } from '../../utils/data';

function TestCallButton({
  disabled, phoneNoToDial, accountSid, authToken, twilioPhoneNo,
}) {
  const onClick = async () => {
    try {
      ToastsStore.info(`Calling number ${phoneNoToDial}`, 5000);
      await testCall(accountSid, authToken, twilioPhoneNo, phoneNoToDial);
    } catch (e) {
      if (e.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        ToastsStore.error(
          `Error in calling ${phoneNoToDial}. Error: ${e.response.data.error
          }`, 5000,
        );
      } else {
        // Something happened in setting up the request that triggered an
        // Error
        ToastsStore.error(
          `Error in calling ${phoneNoToDial}. Error: ${e.message}`, 5000,
        );
      }
    }
  };
  return (
    <Button className="button-style2" disabled={disabled} onClick={onClick}>
      Test call
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

TestCallButton.propTypes = forbidExtraProps({
  disabled: PropTypes.bool.isRequired,
  phoneNoToDial: PropTypes.string.isRequired,
  accountSid: PropTypes.string.isRequired,
  authToken: PropTypes.string.isRequired,
  twilioPhoneNo: PropTypes.string.isRequired,
});

SendTestAlertButton.propTypes = forbidExtraProps({
  disabled: PropTypes.bool.isRequired,
  botToken: PropTypes.string.isRequired,
  botChatID: PropTypes.string.isRequired,
});

export default SendTestAlertButton;
