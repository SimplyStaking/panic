const axios = require('axios');

function sendData(url, params, body) {
  return axios.post(url, body, { params });
}

function fetchData(url, params) {
  return axios.get(url, { params });
}

function pingTendermint(tendermintRpcUrl) {
  return sendData('/server/cosmos/tendermint', {},
    { tendermintRpcUrl });
}

function pingPrometheus(prometheusUrl, metric) {
  return sendData('/server/common/prometheus', {},
    { prometheusUrl, metric });
}

function deleteConfigs() {
  return sendData('/server/config/delete', {}, {});
}

function pingRepo(url) {
  return fetchData(url);
}

function pingDockerHub(repository) {
  return sendData('/server/dockerhub/repository', {}, { repository });
}

function getConfigPaths() {
  return fetchData('/server/paths', {}, {});
}

function getConfig(configType, fileName, chainName, baseChain) {
  return fetchData('/server/config', {
    configType,
    fileName,
    chainName,
    baseChain,
  });
}

function sendConfig(configType, fileName, chainName, baseChain, config) {
  return sendData('/server/config', {
    configType, fileName, chainName, baseChain,
  }, { config });
}

function loadAccounts() {
  return fetchData('/server/account/usernames', {}, {});
}

function saveAccount(username, password) {
  return sendData('/server/account/save', {}, { username, password });
}

function deleteAccount(username) {
  return sendData('/server/account/delete', {}, { username });
}

function sendTestEmail(smtp, from, to, user, pass, port) {
  return sendData('/server/email/test', {}, {
    smtp, from, to, user, pass, port,
  });
}

function sendTestPagerDuty(apiToken, integrationKey) {
  return sendData('/server/pagerduty/test', {}, {
    apiToken, integrationKey,
  });
}

function sendTestOpsGenie(apiKey, eu) {
  return sendData('/server/opsgenie/test', {}, {
    apiKey, eu,
  });
}

function testCall(accountSid, authToken, twilioPhoneNumber,
  phoneNumberToDial) {
  return sendData('/server/twilio/test', {}, {
    accountSid, authToken, twilioPhoneNumber, phoneNumberToDial,
  });
}

function authenticate(username, password) {
  return sendData('/server/login', {}, { username, password });
}

function refreshAccessToken() {
  return sendData('/server/refresh', {}, {});
}

// This function is used to send POST requests
// to the Slack API. This format is required
// since CORS was intervening with the post request.
// An OPTIONS request was being sent by axion
// which is not supported in the Slack API.
// This is explained further below:
// https://stackoverflow.com/questions/41042786/cors-issue-using-axios-with-slack-api
function sendSlackMessage(url, data) {
  return axios.post(url, JSON.stringify(data), {
    withCredentials: false,
    // eslint-disable-next-line no-shadow
    transformRequest: [(data, headers) => {
      // eslint-disable-next-line no-param-reassign
      delete headers.post['Content-Type'];
      return data;
    }],
  });
}

export {
  fetchData, testCall, sendData, sendTestEmail, pingTendermint, pingRepo,
  authenticate, sendTestPagerDuty, sendTestOpsGenie, refreshAccessToken,
  sendConfig, saveAccount, deleteAccount, getConfigPaths, getConfig,
  loadAccounts, deleteConfigs, pingDockerHub, pingPrometheus, sendSlackMessage,
};
