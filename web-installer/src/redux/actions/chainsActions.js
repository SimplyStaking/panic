import {
  ADD_CHAIN, ADD_NODE, ADD_REPOSITORY, REMOVE_NODE, REMOVE_REPOSITORY,
  ADD_KMS, REMOVE_KMS, ADD_CHANNEL, REMOVE_CHANNEL, SET_ALERTS,
  ADD_CONFIG, REMOVE_CONFIG, ADD_TELEGRAM_CHANNEL, REMOVE_TELEGRAM_CHANNEL,
  ADD_TWILIO_CHANNEL, REMOVE_TWILIO_CHANNEL, ADD_EMAIL_CHANNEL,
  REMOVE_EMAIL_CHANNEL, ADD_PAGERDUTY_CHANNEL, REMOVE_PAGERDUTY_CHANNEL,
  ADD_OPSGENIE_CHANNEL, REMOVE_OPSGENIE_CHANNEL, UPDATE_WARNING_DELAY,
  UPDATE_WARNING_REPEAT, UPDATE_WARNING_THRESHOLD, UPDATE_WARNING_TIMEWINDOW,
  UPDATE_WARNING_ENABLED,
} from './types';

export function addChain(payload) {
  return {
    type: ADD_CHAIN,
    payload,
  };
}

export function addNode(payload) {
  return {
    type: ADD_NODE,
    payload,
  };
}

export function removeNode(payload) {
  return {
    type: REMOVE_NODE,
    payload,
  };
}

export function addRepository(payload) {
  return {
    type: ADD_REPOSITORY,
    payload,
  };
}

export function removeRepository(payload) {
  return {
    type: REMOVE_REPOSITORY,
    payload,
  };
}

export function addKMS(payload) {
  return {
    type: ADD_KMS,
    payload,
  };
}

export function removeKMS(payload) {
  return {
    type: REMOVE_KMS,
    payload,
  };
}

export function addChannel(payload) {
  return {
    type: ADD_CHANNEL,
    payload,
  };
}

export function removeChannel(payload) {
  return {
    type: REMOVE_CHANNEL,
    payload,
  };
}

export function setAlerts(payload) {
  return {
    type: SET_ALERTS,
    payload,
  };
}

export function addConfig(payload) {
  return {
    type: ADD_CONFIG,
    payload,
  };
}

export function removeConfig(payload) {
  return {
    type: REMOVE_CONFIG,
    payload,
  };
}

export function addTelegramChannel(payload) {
  return {
    type: ADD_TELEGRAM_CHANNEL,
    payload,
  };
}

export function removeTelegramChannel(payload) {
  return {
    type: REMOVE_TELEGRAM_CHANNEL,
    payload,
  };
}

export function addTwilioChannel(payload) {
  return {
    type: ADD_TWILIO_CHANNEL,
    payload,
  };
}

export function removeTwilioChannel(payload) {
  return {
    type: REMOVE_TWILIO_CHANNEL,
    payload,
  };
}

export function addEmailChannel(payload) {
  return {
    type: ADD_EMAIL_CHANNEL,
    payload,
  };
}

export function removeEmailChannel(payload) {
  return {
    type: REMOVE_EMAIL_CHANNEL,
    payload,
  };
}

export function addPagerDutyChannel(payload) {
  return {
    type: ADD_PAGERDUTY_CHANNEL,
    payload,
  };
}

export function removePagerDutyChannel(payload) {
  return {
    type: REMOVE_PAGERDUTY_CHANNEL,
    payload,
  };
}

export function addOpsGenieChannel(payload) {
  return {
    type: ADD_OPSGENIE_CHANNEL,
    payload,
  };
}

export function removeOpsGenieChannel(payload) {
  return {
    type: REMOVE_OPSGENIE_CHANNEL,
    payload,
  };
}

export function updateWarningDelay(payload) {
  return {
    type: UPDATE_WARNING_DELAY,
    payload,
  };
}

export function updateWarningRepeat(payload) {
  return {
    type: UPDATE_WARNING_REPEAT,
    payload,
  };
}

export function updateWarningThreshold(payload) {
  return {
    type: UPDATE_WARNING_THRESHOLD,
    payload,
  };
}

export function updateWarningTimeWindow(payload) {
  return {
    type: UPDATE_WARNING_TIMEWINDOW,
    payload,
  };
}

export function updateWarningEnabled(payload) {
  return {
    type: UPDATE_WARNING_ENABLED,
    payload,
  };
}
