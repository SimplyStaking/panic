import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import { Button, Box } from '@material-ui/core';
import CancelIcon from '@material-ui/icons/Cancel';
import { ToastsStore } from 'react-toasts';
import {
  authenticate, fetchData, sendTestEmail, testCall, pingRepo, sendTestPagerDuty,
  sendTestOpsGenie, pingTendermint, pingCosmosPrometheus, pingNodeExporter,
  saveAccount, deleteAccount,
} from './data';
import sleep from './time';

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

function SendTestOpsGenieButton({ disabled, apiKey, eu }) {
  const onClick = async () => {
    try {
      ToastsStore.info('Sending test OpsGenie alert.', 5000);
      await sendTestOpsGenie(apiKey, eu);
      ToastsStore.success('Successfully send alert!', 5000);
    } catch (e) {
      if (e.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        ToastsStore.error(
          `Error in sending alert to OpsGenie. Error: ${e.response.data.error
          }`, 5000,
        );
      } else {
        // Something happened in setting up the request that triggered an
        // Error
        ToastsStore.error(
          `Error in sending alert to OpsGenie. Error: ${e.message}`, 5000,
        );
      }
    }
  };
  return (
    <Button
      variant="outlined"
      size="large"
      disabled={disabled}
      onClick={onClick}
    >
      <Box px={2}>
        Test
      </Box>
    </Button>
  );
}

function SendTestPagerDutyButton({ disabled, apiToken, integrationKey }) {
  const onClick = async () => {
    try {
      ToastsStore.info('Sending test PagerDuty alert.', 5000);
      await sendTestPagerDuty(apiToken, integrationKey);
      ToastsStore.success('Successfully send alert!', 5000);
    } catch (e) {
      if (e.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        ToastsStore.error(
          `Error in sending alert to PagerDuty. Error: ${e.response.data.error
          }`, 5000,
        );
      } else {
        // Something happened in setting up the request that triggered an
        // Error
        ToastsStore.error(
          `Error in sending alert to PagerDuty. Error: ${e.message}`, 5000,
        );
      }
    }
  };
  return (
    <Button
      variant="outlined"
      size="large"
      disabled={disabled}
      onClick={onClick}
    >
      <Box px={2}>
        Test
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

function PingRepoButton({ disabled, repo }) {
  const onClick = async () => {
    try {
      ToastsStore.info(`Connecting with repo ${repo}`, 5000);
      // Remove last '/' to connect with https://api.github.com/repos/repoPage`.
      await pingRepo(`https://api.github.com/repos/${
        repo.substring(0, repo.length - 1)
      }`);
      ToastsStore.success('Successfully connected', 5000);
    } catch (e) {
      if (e.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        ToastsStore.error(`Could not connect with repo ${repo}. Error: ${
          e.response.data.message}`, 5000);
      } else {
        // Something happened in setting up the request that triggered an Error
        ToastsStore.error(
          `Could not connect with repo ${repo}. Error: ${e.message}`, 5000,
        );
      }
    }
  };
  return (
    <Button variant="outlined" size="large" disabled={disabled} onClick={onClick}>
      <Box px={2}>
        Test Repository
      </Box>
    </Button>
  );
}

function DeleteAccount({ username, removeFromRedux }) {
  const onClick = async () => {
    try {
      ToastsStore.info(`Deleting account ${username}`, 5000);
      // First remove from the database
      await deleteAccount(username);
      // Then remove from redux
      removeFromRedux(username);
      ToastsStore.success('Successfully removed account', 5000);
    } catch (e) {
      if (e.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        ToastsStore.error(`Could not remove account from database ${username}. Error: ${
          e.response.data.message}`, 5000);
      } else {
        // Something happened in setting up the request that triggered an Error
        ToastsStore.error(
          `Could not remove account from database ${username}. Error: ${e.message}`, 5000,
        );
      }
    }
  };
  return (
    <Button
      onClick={onClick}
    >
      <CancelIcon />
    </Button>
  );
}

function AddAccount({ username, password, disabled }) {
  const onClick = async () => {
    try {
      ToastsStore.info(`Saving account ${username}`, 5000);

      await saveAccount(username, password);

      ToastsStore.success('Successfully added new account', 5000);
    } catch (e) {
      if (e.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        ToastsStore.error(`Could not save account in databse ${username}. Error: ${
          e.response.data.message}`, 5000);
      } else {
        // Something happened in setting up the request that triggered an Error
        ToastsStore.error(
          `Could not save account in database ${username}. Error: ${e.message}`, 5000,
        );
      }
    }
  };
  return (
    <Button
      type="submit"
      variant="outlined"
      size="large"
      disabled={disabled}
      onClick={onClick}
    >
      <Box px={2}>
        Add Account
      </Box>
    </Button>
  );
}

function PingCosmosButton({
  disabled, tendermintRPCURL, prometheusURL, exporterURL,
}) {
  const onClick = async () => {
    // Check if the tendermint RPC URL given works properly
    if (tendermintRPCURL) {
      try {
        ToastsStore.info(`Connecting with Tendermint RPC Url ${tendermintRPCURL}`, 5000);
        await pingTendermint(tendermintRPCURL);
        ToastsStore.success('Successfully connected', 5000);
      } catch (e) {
        if (e.response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          ToastsStore.error(`Could not connect with Tendermint RPC Url ${tendermintRPCURL}. Error: ${
            e.response.data.message}`, 5000);
        } else {
          // Something happened in setting up the request that triggered an Error
          ToastsStore.error(
            `Could not connect with Tendermint RPC Url ${tendermintRPCURL}. Error: ${e.message}`, 5000,
          );
        }
      }
    }

    // Check if the prometheus url given works properly
    if (prometheusURL) {
      try {
        ToastsStore.info(`Connecting with Prometheus Url ${prometheusURL}`, 5000);
        await pingCosmosPrometheus(prometheusURL);
        ToastsStore.success('Successfully connected', 5000);
      } catch (e) {
        if (e.response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          ToastsStore.error(`Could not connect with prometheus url ${prometheusURL}. Error: ${
            e.response.data.message}`, 5000);
        } else {
          // Something happened in setting up the request that triggered an Error
          ToastsStore.error(
            `Could not connect with prometheus url ${prometheusURL}. Error: ${e.message}`, 5000,
          );
        }
      }
    }

    // Check if the node exporter url given works properly
    if (exporterURL) {
      try {
        ToastsStore.info(`Connecting with Node exporter Url ${exporterURL}`, 5000);
        await pingNodeExporter(exporterURL);
        ToastsStore.success('Successfully connected', 5000);
      } catch (e) {
        if (e.response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          ToastsStore.error(`Could not connect with node exporter url ${exporterURL}. Error: ${
            e.response.data.message}`, 5000);
        } else {
          // Something happened in setting up the request that triggered an Error
          ToastsStore.error(
            `Could not connect with node exporter url ${exporterURL}. Error: ${e.message}`, 5000,
          );
        }
      }
    }
  };

  return (
    <Button variant="outlined" size="large" disabled={disabled} onClick={onClick}>
      <Box px={2}>
        Test Node
      </Box>
    </Button>
  );
}

function SaveConfigButton({ onClick, text }) {
  return (
    <Button variant="outlined" size="large" onClick={onClick}>
      <Box px={2}>
        {text}
      </Box>
    </Button>
  );
}
function PingNodeExpoter({ disabled, exporterURL }) {
  const onClick = async () => {
    // Check if the node exporter url given works properly
    if (exporterURL) {
      try {
        ToastsStore.info(`Connecting with Node exporter Url ${exporterURL}`, 5000);
        await pingNodeExporter(exporterURL);
        ToastsStore.success('Successfully connected', 5000);
      } catch (e) {
        if (e.response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          ToastsStore.error(`Could not connect with node exporter url ${exporterURL}. Error: ${
            e.response.data.message}`, 5000);
        } else {
          // Something happened in setting up the request that triggered an Error
          ToastsStore.error(
            `Could not connect with node exporter url ${exporterURL}. Error: ${e.message}`, 5000,
          );
        }
      }
    }
  };

  return (
    <Button variant="outlined" size="large" disabled={disabled} onClick={onClick}>
      <Box px={2}>
        Test Node
      </Box>
    </Button>
  );
}

function LoginButton({
  username, password, disabled, setAuthentication, handleSetCredentialsValid,
  handleSetValidated,
}) {
  const onClick = async () => {
    try {
      ToastsStore.info('Authenticating...', 2000);
      await authenticate(username, password);
      handleSetCredentialsValid(true);
      await sleep(2000);
      ToastsStore.success('Authentication successful', 2000);
      setAuthentication(true);
    } catch (e) {
      if (e.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        ToastsStore.error(
          `Authentication failed. Error: ${e.response.data.error}`, 5000,
        );
      } else {
        // Something happened in setting up the request that triggered an Error
        ToastsStore.error(`Authentication failed. Error: ${e.message}`, 5000);
      }
      handleSetCredentialsValid(false);
    }
    handleSetValidated(true);
  };
  return (
    <Button variant="outlined" size="large" disabled={disabled} onClick={onClick}>
      <Box px={2}>
        Login
      </Box>
    </Button>
  );
}

SendTestOpsGenieButton.propTypes = forbidExtraProps({
  disabled: PropTypes.bool.isRequired,
  apiKey: PropTypes.string.isRequired,
  eu: PropTypes.bool.isRequired,
});

SendTestPagerDutyButton.propTypes = forbidExtraProps({
  disabled: PropTypes.bool.isRequired,
  apiToken: PropTypes.string.isRequired,
  integrationKey: PropTypes.string.isRequired,
});

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

SaveConfigButton.propTypes = forbidExtraProps({
  onClick: PropTypes.func.isRequired,
  text: PropTypes.string.isRequired,
});

LoginButton.propTypes = forbidExtraProps({
  username: PropTypes.string.isRequired,
  password: PropTypes.string.isRequired,
  disabled: PropTypes.bool.isRequired,
  setAuthentication: PropTypes.func.isRequired,
  handleSetCredentialsValid: PropTypes.func.isRequired,
  handleSetValidated: PropTypes.func.isRequired,
});

PingRepoButton.propTypes = forbidExtraProps({
  disabled: PropTypes.bool.isRequired,
  repo: PropTypes.string.isRequired,
});

PingCosmosButton.propTypes = forbidExtraProps({
  disabled: PropTypes.bool.isRequired,
  tendermintRPCURL: PropTypes.string.isRequired,
  prometheusURL: PropTypes.string.isRequired,
  exporterURL: PropTypes.string.isRequired,
});

PingNodeExpoter.propTypes = forbidExtraProps({
  disabled: PropTypes.bool.isRequired,
  exporterURL: PropTypes.string.isRequired,
});

AddAccount.propTypes = forbidExtraProps({
  username: PropTypes.string.isRequired,
  password: PropTypes.string.isRequired,
  disabled: PropTypes.bool.isRequired,
});

DeleteAccount.propTypes = forbidExtraProps({
  username: PropTypes.string.isRequired,
  removeFromRedux: PropTypes.func.isRequired,
});

export {
  SendTestAlertButton, TestCallButton, SendTestEmailButton,
  SendTestPagerDutyButton, SendTestOpsGenieButton, LoginButton,
  PingRepoButton, PingCosmosButton, PingNodeExpoter, SaveConfigButton,
  AddAccount, DeleteAccount,
};
