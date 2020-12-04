const axios = require('axios');

function sendData(url, params, body) {
  return axios.post(url, body, { params });
}

function fetchData(url, params) {
  return axios.get(url, { params });
}

function pingTendermint(tendermint_rpc_url) {
  return sendData('/server/cosmos/tendermint', {},
    { tendermint_rpc_url });
}

function pingCosmosPrometheus(prometheus_url) {
  return sendData('/server/cosmos/prometheus', {},
    { prometheus_url });
}

function pingNodeExporter(exporter_url) {
  return sendData('/server/system/exporter', {},
    { exporter_url });
}

function pingRepo(url) {
  return fetchData(url);
}

function sendConfig(configType, fileName, chain_name, baseChain, config) {
  return sendData('/server/config', {
    configType, fileName, chain_name, baseChain,
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

function sendTestPagerDuty(api_token, integration_key) {
  return sendData('/server/pagerduty/test', {}, {
    api_token, integration_key,
  });
}

function sendTestOpsGenie(apiKey, eu) {
  return sendData('/server/opsgenie/test', {}, {
    apiKey, eu,
  });
}

function testCall(account_sid, auth_token, twilioPhoneNumber,
  phoneNumberToDial) {
  return sendData('/server/twilio/test', {}, {
    account_sid, auth_token, twilioPhoneNumber, phoneNumberToDial,
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
