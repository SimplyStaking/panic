import {
  ADD_CHAIN_SUBSTRATE, ADD_NODE_SUBSTRATE, ADD_REPOSITORY_SUBSTRATE, REMOVE_NODE_SUBSTRATE,
  REMOVE_REPOSITORY_SUBSTRATE, ADD_KMS_SUBSTRATE, REMOVE_KMS_SUBSTRATE, SET_ALERTS_SUBSTRATE,
  ADD_CONFIG_SUBSTRATE, REMOVE_CONFIG_SUBSTRATE, RESET_CONFIG_SUBSTRATE,
  LOAD_CONFIG_SUBSTRATE, ADD_TELEGRAM_CHANNEL_SUBSTRATE,
  REMOVE_TELEGRAM_CHANNEL_SUBSTRATE, ADD_TWILIO_CHANNEL_SUBSTRATE,
  REMOVE_TWILIO_CHANNEL_SUBSTRATE, ADD_EMAIL_CHANNEL_SUBSTRATE,
  REMOVE_EMAIL_CHANNEL_SUBSTRATE, ADD_PAGERDUTY_CHANNEL_SUBSTRATE,
  REMOVE_PAGERDUTY_CHANNEL_SUBSTRATE, ADD_OPSGENIE_CHANNEL_SUBSTRATE,
  REMOVE_OPSGENIE_CHANNEL_SUBSTRATE, UPDATE_WARNING_DELAY_SUBSTRATE,
  UPDATE_WARNING_REPEAT_SUBSTRATE, UPDATE_WARNING_THRESHOLD_SUBSTRATE,
  UPDATE_WARNING_TIMEWINDOW_SUBSTRATE, UPDATE_WARNING_ENABLED_SUBSTRATE,
  UPDATE_CRITICAL_DELAY_SUBSTRATE, UPDATE_CRITICAL_REPEAT_SUBSTRATE,
  UPDATE_CRITICAL_THRESHOLD_SUBSTRATE, UPDATE_CRITICAL_TIMEWINDOW_SUBSTRATE,
  UPDATE_CRITICAL_ENABLED_SUBSTRATE, UPDATE_ALERT_ENABLED_SUBSTRATE,
  UPDATE_ALERT_SEVERTY_LEVEL_SUBSTRATE, UPDATE_ALERT_SEVERTY_ENABLED_SUBSTRATE,
} from './types';

export function addChainSubstrate(payload) {
  return {
    type: ADD_CHAIN_SUBSTRATE,
    payload,
  };
}

export function addNodeSubstrate(payload) {
  return {
    type: ADD_NODE_SUBSTRATE,
    payload,
  };
}

export function removeNodeSubstrate(payload) {
  return {
    type: REMOVE_NODE_SUBSTRATE,
    payload,
  };
}

export function addRepositorySubstrate(payload) {
  return {
    type: ADD_REPOSITORY_SUBSTRATE,
    payload,
  };
}

export function removeRepositorySubstrate(payload) {
  return {
    type: REMOVE_REPOSITORY_SUBSTRATE,
    payload,
  };
}

export function addKMSSubstrate(payload) {
  return {
    type: ADD_KMS_SUBSTRATE,
    payload,
  };
}

export function removeKMSSubstrate(payload) {
  return {
    type: REMOVE_KMS_SUBSTRATE,
    payload,
  };
}

export function setAlertsSubstrate(payload) {
  return {
    type: SET_ALERTS_SUBSTRATE,
    payload,
  };
}

export function addConfigSubstrate() {
  return {
    type: ADD_CONFIG_SUBSTRATE,
  };
}

export function removeConfigSubstrate(payload) {
  return {
    type: REMOVE_CONFIG_SUBSTRATE,
    payload,
  };
}

export function resetConfigSubstrate() {
  return {
    type: RESET_CONFIG_SUBSTRATE,
  };
}

export function loadConfigSubstrate(payload) {
  return {
    type: LOAD_CONFIG_SUBSTRATE,
    payload,
  };
}

export function addTelegramChannelSubstrate(payload) {
  return {
    type: ADD_TELEGRAM_CHANNEL_SUBSTRATE,
    payload,
  };
}

export function removeTelegramChannelSubstrate(payload) {
  return {
    type: REMOVE_TELEGRAM_CHANNEL_SUBSTRATE,
    payload,
  };
}

export function addTwilioChannelSubstrate(payload) {
  return {
    type: ADD_TWILIO_CHANNEL_SUBSTRATE,
    payload,
  };
}

export function removeTwilioChannelSubstrate(payload) {
  return {
    type: REMOVE_TWILIO_CHANNEL_SUBSTRATE,
    payload,
  };
}

export function addEmailChannelSubstrate(payload) {
  return {
    type: ADD_EMAIL_CHANNEL_SUBSTRATE,
    payload,
  };
}

export function removeEmailChannelSubstrate(payload) {
  return {
    type: REMOVE_EMAIL_CHANNEL_SUBSTRATE,
    payload,
  };
}

export function addPagerDutyChannelSubstrate(payload) {
  return {
    type: ADD_PAGERDUTY_CHANNEL_SUBSTRATE,
    payload,
  };
}

export function removePagerDutyChannelSubstrate(payload) {
  return {
    type: REMOVE_PAGERDUTY_CHANNEL_SUBSTRATE,
    payload,
  };
}

export function addOpsGenieChannelSubstrate(payload) {
  return {
    type: ADD_OPSGENIE_CHANNEL_SUBSTRATE,
    payload,
  };
}

export function removeOpsGenieChannelSubstrate(payload) {
  return {
    type: REMOVE_OPSGENIE_CHANNEL_SUBSTRATE,
    payload,
  };
}

export function updateWarningDelaySubstrate(payload) {
  return {
    type: UPDATE_WARNING_DELAY_SUBSTRATE,
    payload,
  };
}

export function updateWarningRepeatSubstrate(payload) {
  return {
    type: UPDATE_WARNING_REPEAT_SUBSTRATE,
    payload,
  };
}

export function updateWarningThresholdSubstrate(payload) {
  return {
    type: UPDATE_WARNING_THRESHOLD_SUBSTRATE,
    payload,
  };
}

export function updateWarningTimeWindowSubstrate(payload) {
  return {
    type: UPDATE_WARNING_TIMEWINDOW_SUBSTRATE,
    payload,
  };
}

export function updateWarningEnabledSubstrate(payload) {
  return {
    type: UPDATE_WARNING_ENABLED_SUBSTRATE,
    payload,
  };
}

export function updateCriticalDelaySubstrate(payload) {
  return {
    type: UPDATE_CRITICAL_DELAY_SUBSTRATE,
    payload,
  };
}

export function updateCriticalRepeatSubstrate(payload) {
  return {
    type: UPDATE_CRITICAL_REPEAT_SUBSTRATE,
    payload,
  };
}

export function updateCriticalThresholdSubstrate(payload) {
  return {
    type: UPDATE_CRITICAL_THRESHOLD_SUBSTRATE,
    payload,
  };
}

export function updateCriticalTimeWindowSubstrate(payload) {
  return {
    type: UPDATE_CRITICAL_TIMEWINDOW_SUBSTRATE,
    payload,
  };
}

export function updateCriticalEnabledSubstrate(payload) {
  return {
    type: UPDATE_CRITICAL_ENABLED_SUBSTRATE,
    payload,
  };
}

export function updateAlertEnabledSubstrate(payload) {
  return {
    type: UPDATE_ALERT_ENABLED_SUBSTRATE,
    payload,
  };
}

export function updateAlertSeverityLevelSubstrate(payload) {
  return {
    type: UPDATE_ALERT_SEVERTY_LEVEL_SUBSTRATE,
    payload,
  };
}

export function updateAlertSeverityEnabledSubstrate(payload) {
  return {
    type: UPDATE_ALERT_SEVERTY_ENABLED_SUBSTRATE,
    payload,
  };
}
