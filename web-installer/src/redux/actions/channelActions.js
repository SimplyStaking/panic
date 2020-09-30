import {
  ADD_TELEGRAM, REMOVE_TELEGRAM, ADD_TWILIO, REMOVE_TWILIO, ADD_EMAIL,
  REMOVE_EMAIL, ADD_PAGERDUTY, REMOVE_PAGERDUTY, ADD_OPSGENIE, REMOVE_OPSGENIE,
} from './types';

const { v4: uuidv4 } = require('uuid');

export function addTelegram(payload) {
  return {
    type: ADD_TELEGRAM,
    payload: {
      id: uuidv4(),
      botName: payload.botName,
      botToken: payload.botToken,
      chatID: payload.chatID,
      info: payload.info,
      warning: payload.warning,
      critical: payload.critical,
      error: payload.error,
      alerts: payload.alerts,
      commands: payload.commands,
    },
  };
}

export function removeTelegram(payload) {
  return {
    type: REMOVE_TELEGRAM,
    payload,
  };
}

export function addTwilio(payload) {
  return {
    type: ADD_TWILIO,
    payload: {
      id: uuidv4(),
      configName: payload.configName,
      accountSid: payload.accountSid,
      authToken: payload.authToken,
      twilioPhoneNo: payload.twilioPhoneNo,
      twilioPhoneNumbersToDialValid: payload.twilioPhoneNumbersToDialValid,
    },
  };
}

export function removeTwilio(payload) {
  return {
    type: REMOVE_TWILIO,
    payload,
  };
}

export function addEmail(payload) {
  return {
    type: ADD_EMAIL,
    payload: {
      id: uuidv4(),
      configName: payload.configName,
      smtp: payload.smtp,
      emailFrom: payload.emailFrom,
      emailsTo: payload.emailsTo,
      username: payload.username,
      password: payload.password,
      info: payload.info,
      warning: payload.warning,
      critical: payload.critical,
      error: payload.error,
    },
  };
}

export function removeEmail(payload) {
  return {
    type: REMOVE_EMAIL,
    payload,
  };
}

export function addPagerDuty(payload) {
  return {
    type: ADD_PAGERDUTY,
    payload: {
      id: uuidv4(),
      configName: payload.configName,
      apiToken: payload.apiToken,
      integrationKey: payload.integrationKey,
      info: payload.info,
      warning: payload.warning,
      critical: payload.critical,
      error: payload.error,
    },
  };
}

export function removePagerDuty(payload) {
  return {
    type: REMOVE_PAGERDUTY,
    payload,
  };
}

export function addOpsGenie(payload) {
  return {
    type: ADD_OPSGENIE,
    payload: {
      id: uuidv4(),
      configName: payload.configName,
      apiToken: payload.apiToken,
      eu: payload.eu,
      info: payload.info,
      warning: payload.warning,
      critical: payload.critical,
      error: payload.error,
    },
  };
}

export function removeOpsGenie(payload) {
  return {
    type: REMOVE_OPSGENIE,
    payload,
  };
}
