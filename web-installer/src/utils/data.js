const axios = require('axios');

function sendData(url, params, body) {
  return axios.post(url, body, { params });
}

function fetchData(url, params) {
  return axios.get(url, { params });
}

function pingNode(apiUrl, nodeName) {
  return sendData('/server/ping_cosmos', {},
    { apiUrl, nodeName });
}

function pingRepo(url) {
  return fetchData(url);
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

export {
  fetchData, testCall, sendData, sendTestEmail, pingNode, pingRepo,
  authenticate, sendTestPagerDuty, sendTestOpsGenie,
};
