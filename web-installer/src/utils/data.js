const axios = require('axios');

function sendData(url, params, body) {
  return axios.post(url, body, { params });
}

function fetchData(url, params) {
  return axios.get(url, { params });
}

function testCall(accountSid, authToken, twilioPhoneNumber,
  phoneNumberToDial) {
  return sendData('/server/test_twilio', {}, {
    accountSid, authToken, twilioPhoneNumber, phoneNumberToDial,
  });
}

export { fetchData, testCall, sendData };
