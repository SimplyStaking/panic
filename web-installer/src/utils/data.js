const axios = require('axios');

function sendData(url, params, body) {
  return axios.post(url, body, { params });
}

function fetchData(url, params) {
  return axios.get(url, { params });
}

function pingTendermint(tendermintRPCURL) {
  return sendData('/server/cosmos/tendermint', {},
    { tendermintRPCURL });
}

function pingCosmosPrometheus(prometheusURL) {
  return sendData('/server/cosmos/prometheus', {},
    { prometheusURL });
}

function pingNodeExporter(exporterURL) {
  return sendData('/server/system/exporter', {},
    { exporterURL });
}

function pingRepo(url) {
  return fetchData(url);
}

function sendConfig(configType, fileName, chainName, baseChain, config) {
  return sendData('/server/config', {
    configType, fileName, chainName, baseChain,
  }, { config });
}

function saveAccount(username, password) {
  return sendData('/server/account/save', {}, { username, password });
}

function deleteAccount(username) {
  return sendData('/server/account/delete', {}, { username });
}

function sendTestEmail(smtp, from, to, user, pass) {
  return sendData('/server/email/test', {}, {
    smtp, from, to, user, pass,
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
  fetchData, testCall, sendData, sendTestEmail, pingTendermint, pingRepo,
  authenticate, sendTestPagerDuty, sendTestOpsGenie, refreshAccessToken,
  pingCosmosPrometheus, pingNodeExporter, sendConfig, saveAccount,
  deleteAccount,
};
