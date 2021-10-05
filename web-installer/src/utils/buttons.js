import React from 'react';
import Web3 from 'web3';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import Button from 'components/material_ui/CustomButtons/Button';
import CancelIcon from '@material-ui/icons/Cancel';
import { ToastsStore } from 'react-toasts';
import {
  authenticate,
  fetchData,
  sendTestEmail,
  testCall,
  pingRepo,
  sendTestPagerDuty,
  sendTestOpsGenie,
  pingTendermint,
  pingPrometheus,
  saveAccount,
  deleteAccount,
  pingDockerHub,
} from './data';
import sleep from './time';

const { WebClient, LogLevel } = require('@slack/web-api');

// Sends test emails to every email provided in the "to" array.
function SendTestEmailButton({
  disabled, to, smtp, from, user, pass, port,
}) {
  const onClick = async () => {
    to.forEach(async (emailTo) => {
      try {
        ToastsStore.info(`Sending test e-mail to address ${to}`, 5000);
        await sendTestEmail(smtp, from, emailTo, user, pass, port);
        ToastsStore.success('Test e-mail sent successfully, check inbox', 5000);
      } catch (e) {
        if (e.response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          ToastsStore.error(`Could not send test e-mail. Error: ${e.response.data.error}`, 5000);
        } else {
          // Something happened in setting up the request that triggered an error
          ToastsStore.error(`Could not send test e-mail. Error: ${e.message}`, 5000);
        }
      }
    });
  };
  return (
    <Button color="primary" size="md" disabled={disabled} onClick={onClick}>
      Test
    </Button>
  );
}

// Sends test calls to every phone number provided in the "twilioPhoneNo" array.
function TestCallButton({
  disabled,
  twilioPhoneNumbersToDialValid,
  accountSid,
  authToken,
  twilioPhoneNumber,
}) {
  const onClick = async () => {
    twilioPhoneNumbersToDialValid.forEach(async (phoneNumberToDial) => {
      try {
        ToastsStore.info(`Calling number ${phoneNumberToDial}`, 5000);
        await testCall(accountSid, authToken, twilioPhoneNumber, phoneNumberToDial);
      } catch (e) {
        if (e.response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          ToastsStore.error(
            `Error in calling ${phoneNumberToDial}. Error: ${e.response.data.error}`,
            5000,
          );
        } else {
          // Something happened in setting up the request that triggered an
          // Error
          ToastsStore.error(`Error in calling ${phoneNumberToDial}. Error: ${e.message}`, 5000);
        }
      }
    });
  };
  return (
    <Button color="primary" size="md" disabled={disabled} onClick={onClick}>
      Test
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
          `Error in sending alert to OpsGenie. Error: ${e.response.data.error}`,
          5000,
        );
      } else {
        // Something happened in setting up the request that triggered an
        // Error
        ToastsStore.error(`Error in sending alert to OpsGenie. Error: ${e.message}`, 5000);
      }
    }
  };
  return (
    <Button color="primary" size="md" disabled={disabled} onClick={onClick}>
      Test
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
          `Error in sending alert to PagerDuty. Error: ${e.response.data.error}`,
          5000,
        );
      } else {
        // Something happened in setting up the request that triggered an
        // Error
        ToastsStore.error(`Error in sending alert to PagerDuty. Error: ${e.message}`, 5000);
      }
    }
  };
  return (
    <Button color="primary" size="md" disabled={disabled} onClick={onClick}>
      Test
    </Button>
  );
}

function SendTestSlackButton({ disabled, botToken, botChannelId }) {
  const onClick = async () => {
    try {
      ToastsStore.info(
        'Sending test alert. Make sure to check the ID of the slack channel is'
        + ` ${botChannelId}`, 5000,
      );

      // WebClient instantiates a client that can call API methods
      // When using Bolt, you can use either `app.client` or the `client`
      // passed to listeners.
      const client = new WebClient(botToken, {
        // LogLevel can be imported and used to make debugging simpler
        logLevel: LogLevel.DEBUG,
      });

      // Call the chat.postMessage method using the built-in WebClient
      await client.chat.postMessage({
        channel: botChannelId,
        text: '*Test Alert*',
      });

      ToastsStore.success('Test alert sent successfully', 5000);
    } catch (e) {
      if (e.response) {
        // The request was made and the server responded with a status code that
        // falls out of the range of 2xx
        ToastsStore.error(`Could not send test alert. Error: ${e.response.data.description}`, 5000);
      } else {
        // Something happened in setting up the request that triggered an Error
        ToastsStore.error(`Could not send test alert. Error: ${e.message}`, 5000);
      }
    }
  };
  return (
    <Button color="primary" size="md" disabled={disabled} onClick={onClick}>
      Test
    </Button>
  );
}

function SendTestTelegramButton({ disabled, botChatID, botToken }) {
  const onClick = async () => {
    try {
      ToastsStore.info(
        'Sending test alert. Make sure to check the chat corresponding with '
        + `chat id ${botChatID}`,
        5000,
      );
      await fetchData(`https://api.telegram.org/bot${botToken}/sendMessage`, {
        chat_id: botChatID,
        text: '*Test Alert*',
        parse_mode: 'Markdown',
      });
      ToastsStore.success('Test alert sent successfully', 5000);
    } catch (e) {
      if (e.response) {
        // The request was made and the server responded with a status code that
        // falls out of the range of 2xx
        ToastsStore.error(`Could not send test alert. Error: ${e.response.data.description}`, 5000);
      } else {
        // Something happened in setting up the request that triggered an Error
        ToastsStore.error(`Could not send test alert. Error: ${e.message}`, 5000);
      }
    }
  };
  return (
    <Button color="primary" size="md" disabled={disabled} onClick={onClick}>
      Test
    </Button>
  );
}

function PingRepoButton({ disabled, repo }) {
  const onClick = async () => {
    try {
      ToastsStore.info(`Connecting with repo ${repo}`, 5000);
      // Remove last '/' to connect with https://api.github.com/repos/repoPage`.
      await pingRepo(`https://api.github.com/repos/${repo.substring(0, repo.length - 1)}`);
      ToastsStore.success('Successfully connected', 5000);
    } catch (e) {
      if (e.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        ToastsStore.error(
          `Could not connect with repo ${repo}. Error: ${e.response.data.message}`,
          5000,
        );
      } else {
        // Something happened in setting up the request that triggered an Error
        ToastsStore.error(`Could not connect with repo ${repo}. Error: ${e.message}`, 5000);
      }
    }
  };
  return (
    <Button color="primary" size="md" disabled={disabled} onClick={onClick}>
      Test Repo
    </Button>
  );
}

function PingDockerHubButton({ disabled, name }) {
  const onClick = async () => {
    try {
      ToastsStore.info(`Connecting with repo ${name}`, 5000);
      await pingDockerHub(name);
      ToastsStore.success('Successfully connected', 5000);
    } catch (e) {
      if (e.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        ToastsStore.error(
          `Could not connect with repo ${name}. Error: ${e.response.data.message}`,
          5000,
        );
      } else {
        // Something happened in setting up the request that triggered an Error
        ToastsStore.error(`Could not connect with repo ${name}. Error: ${e.message}`, 5000);
      }
    }
  };
  return (
    <Button color="primary" size="md" disabled={disabled} onClick={onClick}>
      Test Docker
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
        ToastsStore.error(
          `Could not remove account from database ${username}. Error: ${e.response.data.message}`,
          5000,
        );
      } else {
        // Something happened in setting up the request that triggered an Error
        ToastsStore.error(
          `Could not remove account from database ${username}. Error: ${e.message}`,
          5000,
        );
      }
    }
  };
  return (
    <Button onClick={onClick}>
      <CancelIcon />
    </Button>
  );
}

function AddAccount({
  username, password, disabled, saveUserDetails,
}) {
  const onClick = async () => {
    try {
      ToastsStore.info(`Saving account ${username}`, 5000);

      await saveAccount(username, password);
      saveUserDetails(username);
      ToastsStore.success('Successfully added new account', 5000);
    } catch (e) {
      if (e.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        ToastsStore.error(
          `Could not save account ${username} in database. Error: ${e.response.data.message}`,
          5000,
        );
      } else {
        // Something happened in setting up the request that triggered an Error
        ToastsStore.error(
          `Could not save account ${username} in database. Error: ${e.message}`,
          5000,
        );
      }
    }
  };
  return (
    <Button color="primary" size="md" disabled={disabled} onClick={onClick}>
      Add
    </Button>
  );
}

function PingTendermint({ disabled, tendermintRpcUrl }) {
  const onClick = async () => {
    try {
      ToastsStore.info(`Connecting with Tendermint RPC URL ${tendermintRpcUrl}`, 5000);
      await pingTendermint(tendermintRpcUrl);
      ToastsStore.success('Successfully connected', 5000);
    } catch (e) {
      if (e.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        ToastsStore.error(
          `Could not connect with the Tendermint RPC URL ${tendermintRpcUrl}. Error: ${e.response.data.message}`,
          5000,
        );
      } else {
        // Something happened in setting up the request that triggered an Error
        ToastsStore.error(
          `Could not connect with Tendermint RPC URL ${tendermintRpcUrl}. Error: ${e.message}`,
          5000,
        );
      }
    }
  };
  return (
    <Button color="primary" size="md" disabled={disabled} onClick={onClick}>
      Test
    </Button>
  );
}

function PingMultiplePrometheus({ disabled, prometheusUrls, metric }) {
  const onClick = async () => {
    prometheusUrls.forEach(async (prometheusUrl) => {
      try {
        ToastsStore.info(`Connecting with Prometheus URL ${prometheusUrl}`, 5000);
        await pingPrometheus(prometheusUrl, metric);
        ToastsStore.success('Successfully connected', 5000);
      } catch (e) {
        if (e.response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          ToastsStore.error(
            `Could not connect with Prometheus URLs ${prometheusUrl}. Error: ${e.response.data.message}`,
            5000,
          );
        } else {
          // Something happened in setting up the request that triggered an Error
          ToastsStore.error(
            `Could not connect with Prometheus URL ${prometheusUrl}. Error: ${e.message}`,
            5000,
          );
        }
      }
    });
  };
  return (
    <Button color="primary" size="md" disabled={disabled} onClick={onClick}>
      Test
    </Button>
  );
}

function PingPrometheus({ disabled, prometheusUrl, metric }) {
  const onClick = async () => {
    try {
      ToastsStore.info(`Connecting with Prometheus URL ${prometheusUrl}`, 5000);
      await pingPrometheus(prometheusUrl, metric);
      ToastsStore.success('Successfully connected', 5000);
    } catch (e) {
      if (e.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        ToastsStore.error(
          `Could not connect with Prometheus URL ${prometheusUrl}. Error: ${e.response.data.message}`,
          5000,
        );
      } else {
        // Something happened in setting up the request that triggered an Error
        ToastsStore.error(
          `Could not connect with Prometheus URL ${prometheusUrl}. Error: ${e.message}`,
          5000,
        );
      }
    }
  };
  return (
    <Button color="primary" size="md" disabled={disabled} onClick={onClick}>
      Test
    </Button>
  );
}

function PingRPC({ disabled, httpUrl }) {
  const onClick = async () => {
    try {
      ToastsStore.info(`Connecting with Node Http URL ${httpUrl}`, 5000);
      const web3 = new Web3(new Web3.providers.HttpProvider(httpUrl));
      await web3.eth.isSyncing();
      ToastsStore.success('Successfully connected', 5000);
    } catch (e) {
      if (e.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        ToastsStore.error(
          `Could not connect with RPC URL ${httpUrl}. Error: ${e.response.data.message}`,
          5000,
        );
      } else {
        // Something happened in setting up the request that triggered an Error
        ToastsStore.error(`Could not connect with RPC URL ${httpUrl}. Error: ${e.message}`, 5000);
      }
    }
  };
  return (
    <Button color="primary" size="md" disabled={disabled} onClick={onClick}>
      Test
    </Button>
  );
}

function SaveConfigButton({ onClick }) {
  return (
    <Button onClick={onClick} size="lg" color="primary" fullWidth>
      Finish
    </Button>
  );
}

function BackButton({ onClick }) {
  return (
    <Button onClick={onClick} size="lg" color="primary" fullWidth>
      Back
    </Button>
  );
}

function StartNewButton({ onClick }) {
  return (
    <Button onClick={onClick} size="lg" color="primary" fullWidth>
      Start New
    </Button>
  );
}

function LoadConfigButton({ onClick }) {
  return (
    <Button onClick={onClick} size="lg" color="primary" fullWidth>
      Load Config
    </Button>
  );
}

function LoginButton({
  username, password, disabled, setAuthentication,
}) {
  const onClick = async () => {
    try {
      ToastsStore.info('Authenticating...', 2000);
      await authenticate(username, password);
      await sleep(2000);
      ToastsStore.success('Authentication successful', 2000);
      setAuthentication(true);
    } catch (e) {
      if (e.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        ToastsStore.error(`${e.response.data.error}`, 5000);
      } else {
        // Something happened in setting up the request that triggered an Error
        ToastsStore.error(`${e.message}`, 5000);
      }
    }
  };
  return (
    <Button color="primary" size="lg" disabled={disabled} onClick={onClick} fullWidth>
      Get started
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
  port: PropTypes.number.isRequired,
  from: PropTypes.string.isRequired,
  user: PropTypes.string.isRequired,
  pass: PropTypes.string.isRequired,
});

TestCallButton.propTypes = forbidExtraProps({
  disabled: PropTypes.bool.isRequired,
  accountSid: PropTypes.string.isRequired,
  authToken: PropTypes.string.isRequired,
  twilioPhoneNumber: PropTypes.string.isRequired,
  twilioPhoneNumbersToDialValid: PropTypes.arrayOf(PropTypes.string.isRequired).isRequired,
});

SendTestTelegramButton.propTypes = forbidExtraProps({
  disabled: PropTypes.bool.isRequired,
  botToken: PropTypes.string.isRequired,
  botChatID: PropTypes.string.isRequired,
});

SendTestSlackButton.propTypes = forbidExtraProps({
  disabled: PropTypes.bool.isRequired,
  botToken: PropTypes.string.isRequired,
  botChannelId: PropTypes.string.isRequired,
});

SaveConfigButton.propTypes = forbidExtraProps({
  onClick: PropTypes.func.isRequired,
});

BackButton.propTypes = forbidExtraProps({
  onClick: PropTypes.func.isRequired,
});

LoadConfigButton.propTypes = forbidExtraProps({
  onClick: PropTypes.func.isRequired,
});

StartNewButton.propTypes = forbidExtraProps({
  onClick: PropTypes.func.isRequired,
});

LoginButton.propTypes = forbidExtraProps({
  username: PropTypes.string.isRequired,
  password: PropTypes.string.isRequired,
  disabled: PropTypes.bool.isRequired,
  setAuthentication: PropTypes.func.isRequired,
});

PingRepoButton.propTypes = forbidExtraProps({
  disabled: PropTypes.bool.isRequired,
  repo: PropTypes.string.isRequired,
});

PingDockerHubButton.propTypes = forbidExtraProps({
  disabled: PropTypes.bool.isRequired,
  name: PropTypes.string.isRequired,
});

PingRPC.propTypes = forbidExtraProps({
  disabled: PropTypes.bool.isRequired,
  httpUrl: PropTypes.string.isRequired,
});

PingMultiplePrometheus.propTypes = forbidExtraProps({
  disabled: PropTypes.bool.isRequired,
  prometheusUrls: PropTypes.arrayOf(PropTypes.string.isRequired).isRequired,
  metric: PropTypes.string.isRequired,
});

PingPrometheus.propTypes = forbidExtraProps({
  disabled: PropTypes.bool.isRequired,
  prometheusUrl: PropTypes.string.isRequired,
  metric: PropTypes.string.isRequired,
});

PingTendermint.propTypes = forbidExtraProps({
  disabled: PropTypes.bool.isRequired,
  tendermintRpcUrl: PropTypes.string.isRequired,
});

AddAccount.propTypes = forbidExtraProps({
  username: PropTypes.string.isRequired,
  password: PropTypes.string.isRequired,
  disabled: PropTypes.bool.isRequired,
  saveUserDetails: PropTypes.func.isRequired,
});

DeleteAccount.propTypes = forbidExtraProps({
  username: PropTypes.string.isRequired,
  removeFromRedux: PropTypes.func.isRequired,
});

export {
  SendTestTelegramButton,
  TestCallButton,
  SendTestSlackButton,
  SendTestEmailButton,
  SendTestPagerDutyButton,
  SendTestOpsGenieButton,
  LoginButton,
  PingRepoButton,
  PingTendermint,
  PingPrometheus,
  SaveConfigButton,
  LoadConfigButton,
  AddAccount,
  DeleteAccount,
  StartNewButton,
  BackButton,
  PingDockerHubButton,
  PingRPC,
};
