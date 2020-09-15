import {
  ADD_CHAIN, ADD_NODE, ADD_REPOSITORY, REMOVE_NODE, REMOVE_REPOSITORY,
  ADD_KMS, REMOVE_KMS, ADD_CHANNEL, REMOVE_CHANNEL, SET_ALERTS,
  ADD_CONFIG, REMOVE_CONFIG, RESET_CONFIG, LOAD_CONFIG, ADD_TELEGRAM_CHANNEL,
  REMOVE_TELEGRAM_CHANNEL, ADD_TWILIO_CHANNEL, REMOVE_TWILIO_CHANNEL,
  ADD_EMAIL_CHANNEL, REMOVE_EMAIL_CHANNEL, ADD_PAGERDUTY_CHANNEL,
  REMOVE_PAGERDUTY_CHANNEL, ADD_OPSGENIE_CHANNEL, REMOVE_OPSGENIE_CHANNEL,
  UPDATE_WARNING_DELAY, UPDATE_WARNING_REPEAT, UPDATE_WARNING_THRESHOLD,
  UPDATE_WARNING_TIMEWINDOW, UPDATE_WARNING_ENABLED, UPDATE_CRITICAL_DELAY,
  UPDATE_CRITICAL_REPEAT, UPDATE_CRITICAL_THRESHOLD, UPDATE_CRITICAL_TIMEWINDOW,
  UPDATE_CRITICAL_ENABLED, UPDATE_ALERT_ENABLED, UPDATE_ALERT_SEVERTY_LEVEL,
  UPDATE_ALERT_SEVERTY_ENABLED,
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

export function addConfig() {
  return {
    type: ADD_CONFIG,
  };
}

export function removeConfig(payload) {
  return {
    type: REMOVE_CONFIG,
    payload,
  };
}

export function resetConfig() {
  return {
    type: RESET_CONFIG,
  };
}

export function loadConfig(payload) {
  return {
    type: LOAD_CONFIG,
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

export function updateCriticalDelay(payload) {
  return {
    type: UPDATE_CRITICAL_DELAY,
    payload,
  };
}

export function updateCriticalRepeat(payload) {
  return {
    type: UPDATE_CRITICAL_REPEAT,
    payload,
  };
}

export function updateCriticalThreshold(payload) {
  return {
    type: UPDATE_CRITICAL_THRESHOLD,
    payload,
  };
}

export function updateCriticalTimeWindow(payload) {
  return {
    type: UPDATE_CRITICAL_TIMEWINDOW,
    payload,
  };
}

export function updateCriticalEnabled(payload) {
  return {
    type: UPDATE_CRITICAL_ENABLED,
    payload,
  };
}

export function updateAlertEnabled(payload) {
  return {
    type: UPDATE_ALERT_ENABLED,
    payload,
  };
}

export function updateAlertSeverityLevel(payload) {
  return {
    type: UPDATE_ALERT_SEVERTY_LEVEL,
    payload,
  };
}

export function updateAlertSeverityEnabled(payload) {
  return {
    type: UPDATE_ALERT_SEVERTY_ENABLED,
    payload,
  };
}
