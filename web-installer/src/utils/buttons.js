import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import { Box } from '@material-ui/core';
import Button from "components/material_ui/CustomButtons/Button.js";
import CancelIcon from '@material-ui/icons/Cancel';
import { ToastsStore } from 'react-toasts';
import {
  authenticate, fetchData, sendTestEmail, testCall, pingRepo, sendTestPagerDuty,
  sendTestOpsGenie, pingTendermint, pingCosmosPrometheus, pingNodeExporter,
  saveAccount, deleteAccount,
} from './data';
import sleep from './time';

// Sends test emails to every email provided in the "to" array.
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
    <Button color="primary" size="md" disabled={disabled} onClick={onClick}>
      Test
    </Button>
  );
}

// Sends test calls to every phone number provided in the "twilioPhoneNum" array.
function TestCallButton({
  disabled, twilioPhoneNumbersToDial, account_sid, authToken, twilioPhoneNum,
}) {
  const onClick = async () => {
    twilioPhoneNumbersToDial.forEach(async (twilioNumber) => {
      try {
        ToastsStore.info(`Calling number ${twilioNumber}`, 5000);
        await testCall(account_sid, authToken, twilioPhoneNum, twilioNumber);
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
    <Button color="primary" size="md" disabled={disabled} onClick={onClick}>
      Test
    </Button>
  );
}

function SendTestPagerDutyButton({ disabled, api_token, integrationKey }) {
  const onClick = async () => {
    try {
      ToastsStore.info('Sending test PagerDuty alert.', 5000);
      await sendTestPagerDuty(api_token, integrationKey);
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
    <Button color="primary" size="md" disabled={disabled} onClick={onClick}>
      Test
    </Button>
  );
}

function SendTestAlertButton({ disabled, botChatID, bot_token }) {
  const onClick = async () => {
    try {
      ToastsStore.info(
        'Sending test alert. Make sure to check the chat corresponding with '
        + `chat id ${botChatID}`, 5000,
      );
      await fetchData(
        `https://api.telegram.org/bot${bot_token}/sendMessage`, {
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
    <Button color="primary" size="md" disabled={disabled} onClick={onClick}>
      Test Repo
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
    <Button color="primary" size="md" disabled={disabled} onClick={onClick}>
      Add
    </Button>
  );
}

function PingCosmosButton({
  disabled, tendermintRpcUrl, prometheusUrl, exporter_url,
}) {
  const onClick = async () => {
    // Check if the tendermint RPC URL given works properly
    if (tendermintRpcUrl) {
      try {
        ToastsStore.info(`Connecting with Tendermint RPC Url ${tendermintRpcUrl}`, 5000);
        await pingTendermint(tendermintRpcUrl);
        ToastsStore.success('Successfully connected', 5000);
      } catch (e) {
        if (e.response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          ToastsStore.error(`Could not connect with Tendermint RPC Url ${tendermintRpcUrl}. Error: ${
            e.response.data.message}`, 5000);
        } else {
          // Something happened in setting up the request that triggered an Error
          ToastsStore.error(
            `Could not connect with Tendermint RPC Url ${tendermintRpcUrl}. Error: ${e.message}`, 5000,
          );
        }
      }
    }

    // Check if the prometheus url given works properly
    if (prometheusUrl) {
      try {
        ToastsStore.info(`Connecting with Prometheus Url ${prometheusUrl}`, 5000);
        await pingCosmosPrometheus(prometheusUrl);
        ToastsStore.success('Successfully connected', 5000);
      } catch (e) {
        if (e.response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          ToastsStore.error(`Could not connect with prometheus url ${prometheusUrl}. Error: ${
            e.response.data.message}`, 5000);
        } else {
          // Something happened in setting up the request that triggered an Error
          ToastsStore.error(
            `Could not connect with prometheus url ${prometheusUrl}. Error: ${e.message}`, 5000,
          );
        }
      }
    }

    // Check if the node exporter url given works properly
    if (exporter_url) {
      try {
        ToastsStore.info(`Connecting with Node exporter Url ${exporter_url}`, 5000);
        await pingNodeExporter(exporter_url);
        ToastsStore.success('Successfully connected', 5000);
      } catch (e) {
        if (e.response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          ToastsStore.error(`Could not connect with node exporter url ${exporter_url}. Error: ${
            e.response.data.message}`, 5000);
        } else {
          // Something happened in setting up the request that triggered an Error
          ToastsStore.error(
            `Could not connect with node exporter url ${exporter_url}. Error: ${e.message}`, 5000,
          );
        }
      }
    }
  };

  return (
    <Button color="primary" size="md" disabled={disabled} onClick={onClick}>
      Test Node
    </Button>
  );
}

function SaveConfigButton({ onClick }) {
  return (
    <Button onClick={onClick} size="lg" color="primary">
      Finish
    </Button>
  );
}
function PingNodeExporter({ disabled, exporter_url }) {
  const onClick = async () => {
    // Check if the node exporter url given works properly
    if (exporter_url) {
      try {
        ToastsStore.info(`Connecting with Node exporter Url ${exporter_url}`, 5000);
        await pingNodeExporter(exporter_url);
        ToastsStore.success('Successfully connected', 5000);
      } catch (e) {
        if (e.response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          ToastsStore.error(`Could not connect with node exporter url ${exporter_url}. Error: ${
            e.response.data.message}`, 5000);
        } else {
          // Something happened in setting up the request that triggered an Error
          ToastsStore.error(
            `Could not connect with node exporter url ${exporter_url}. Error: ${e.message}`, 5000,
          );
        }
      }
    }
  };

  return (
    <Button color="primary" size="md" disabled={disabled} onClick={onClick}>
      Test
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
        ToastsStore.error(
          `Authentication failed. Error: ${e.response.data.error}`, 5000,
        );
      } else {
        // Something happened in setting up the request that triggered an Error
        ToastsStore.error(`Authentication failed. Error: ${e.message}`, 5000);
      }
    }
  };
  return (
    <Button color="primary" size="lg" disabled={disabled} onClick={onClick}>
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
  api_token: PropTypes.string.isRequired,
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
  account_sid: PropTypes.string.isRequired,
  authToken: PropTypes.string.isRequired,
  twilioPhoneNum: PropTypes.string.isRequired,
  twilioPhoneNumbersToDial: PropTypes.arrayOf(
    PropTypes.string.isRequired,
  ).isRequired,
});

SendTestAlertButton.propTypes = forbidExtraProps({
  disabled: PropTypes.bool.isRequired,
  bot_token: PropTypes.string.isRequired,
  botChatID: PropTypes.string.isRequired,
});

SaveConfigButton.propTypes = forbidExtraProps({
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

PingCosmosButton.propTypes = forbidExtraProps({
  disabled: PropTypes.bool.isRequired,
  tendermintRpcUrl: PropTypes.string.isRequired,
  prometheusUrl: PropTypes.string.isRequired,
  exporter_url: PropTypes.string.isRequired,
});

PingNodeExporter.propTypes = forbidExtraProps({
  disabled: PropTypes.bool.isRequired,
  exporter_url: PropTypes.string.isRequired,
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
  PingRepoButton, PingCosmosButton, PingNodeExporter, SaveConfigButton,
  AddAccount, DeleteAccount,
};
