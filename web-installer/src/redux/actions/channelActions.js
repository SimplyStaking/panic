import {
  ADD_TELEGRAM, REMOVE_TELEGRAM, ADD_TWILIO, REMOVE_TWILIO, ADD_EMAIL,
  REMOVE_EMAIL, ADD_PAGERDUTY, REMOVE_PAGERDUTY, ADD_OPSGENIE, REMOVE_OPSGENIE,
} from './types';

export function addTelegram(payload) {
  return {
    type: ADD_TELEGRAM,
    payload,
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
