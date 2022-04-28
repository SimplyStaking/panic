const axios = require('axios');

function sendData(url, params, body) {
  return axios.post(url, body, { params });
}

function fetchData(url, params) {
  return axios.get(url, { params });
}

function pingCosmosRestUrl(restUrl) {
  return sendData('/server/cosmos/rest', {}, { restUrl });
}

function pingPrometheus(prometheusUrl, metric) {
  return sendData('/server/common/prometheus', {},
    { prometheusUrl, metric });
}

function pingTendermintRPC(httpUrl) {
  return sendData('/server/cosmos/tendermint', {},
    { httpUrl });
}

function pingEthRPC(httpUrl) {
  return sendData('/server/ethereum/rpc', {},
    { httpUrl });
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

export {
  fetchData, testCall, sendData, sendTestEmail, pingRepo,
  authenticate, sendTestPagerDuty, sendTestOpsGenie, refreshAccessToken,
  sendConfig, saveAccount, deleteAccount, getConfigPaths, getConfig,
  loadAccounts, deleteConfigs, pingDockerHub, pingPrometheus, pingEthRPC,
  pingCosmosRestUrl, pingTendermintRPC,
};
