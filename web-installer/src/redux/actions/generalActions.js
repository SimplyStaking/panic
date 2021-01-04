import {
  UPDATE_PERIODIC,
  ADD_REPOSITORY,
  ADD_SYSTEM,
  REMOVE_REPOSITORY,
  REMOVE_SYSTEM,
  ADD_KMS,
  REMOVE_KMS,
  UPDATE_THRESHOLD_ALERT,
  ADD_TELEGRAM_CHANNEL,
  REMOVE_TELEGRAM_CHANNEL,
  ADD_TWILIO_CHANNEL,
  REMOVE_TWILIO_CHANNEL,
  ADD_EMAIL_CHANNEL,
  REMOVE_EMAIL_CHANNEL,
  ADD_PAGERDUTY_CHANNEL,
  REMOVE_PAGERDUTY_CHANNEL,
  ADD_OPSGENIE_CHANNEL,
  REMOVE_OPSGENIE_CHANNEL,
  LOAD_REPOSITORY,
  LOAD_REPOSITORY_GENERAL,
  LOAD_KMS,
  LOAD_THRESHOLD_ALERTS_GENERAL,
  LOAD_REPEAT_ALERTS_GENERAL,
  LOAD_SYSTEM_GENERAL,
  LOAD_SYSTEM,
} from './types';

const { v4: uuidv4 } = require('uuid');

export function updatePeriodic(payload) {
  return {
    type: UPDATE_PERIODIC,
    payload,
  };
}

export function addRepository(payload) {
  return {
    type: ADD_REPOSITORY,
    payload: {
      id: `repo_${uuidv4()}`,
      parent_id: payload.parent_id,
      repo_name: payload.repo_name,
      monitor_repo: payload.monitor_repo,
    },
  };
}

export function loadRepository(payload) {
  return {
    type: LOAD_REPOSITORY,
    payload,
  };
}

export function removeRepository(payload) {
  return {
    type: REMOVE_REPOSITORY,
    payload,
  };
}

export function addSystem(payload) {
  return {
    type: ADD_SYSTEM,
    payload: {
      id: `system_${uuidv4()}`,
      parent_id: payload.parent_id,
      name: payload.name,
      exporter_url: payload.exporter_url,
      monitor_system: payload.monitor_system,
    },
  };
}

export function loadSystem(payload) {
  return {
    type: LOAD_SYSTEM,
    payload,
  };
}

export function loadSystemGeneral(payload) {
  return {
    type: LOAD_SYSTEM_GENERAL,
    payload,
  };
}

export function removeSystem(payload) {
  return {
    type: REMOVE_SYSTEM,
    payload,
  };
}

export function addKms(payload) {
  return {
    type: ADD_KMS,
    payload: {
      id: `kms_${uuidv4()}`,
      parent_id: payload.parent_id,
      kms_name: payload.kms_name,
      exporter_url: payload.exporter_url,
      monitor_kms: payload.monitor_kms,
    },
  };
}

export function removeKms(payload) {
  return {
    type: REMOVE_KMS,
    payload,
  };
}

export function updateThresholdAlert(payload) {
  return {
    type: UPDATE_THRESHOLD_ALERT,
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

export function loadReposGeneral(payload) {
  return {
    type: LOAD_REPOSITORY_GENERAL,
    payload,
  };
}

export function loadKMS(payload) {
  return {
    type: LOAD_KMS,
    payload,
  };
}

export function loadRepeatAlertsGeneral(payload) {
  return {
    type: LOAD_REPEAT_ALERTS_GENERAL,
    payload,
  };
}

export function loadThresholdAlertsGeneral(payload) {
  return {
    type: LOAD_THRESHOLD_ALERTS_GENERAL,
    payload,
  };
}
