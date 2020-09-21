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
    payload,
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
    payload,
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
    payload,
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
    payload,
  };
}

export function removeOpsGenie(payload) {
  return {
    type: REMOVE_OPSGENIE,
    payload,
  };
}
