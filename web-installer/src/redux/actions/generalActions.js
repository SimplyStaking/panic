import {
  UPDATE_PERIODIC, ADD_REPOSITORY, ADD_SYSTEM, REMOVE_REPOSITORY, REMOVE_SYSTEM,
  ADD_KMS, REMOVE_KMS, UPDATE_THRESHOLD_ALERT, ADD_TELEGRAM_CHANNEL,
  REMOVE_TELEGRAM_CHANNEL, ADD_TWILIO_CHANNEL, REMOVE_TWILIO_CHANNEL,
  ADD_EMAIL_CHANNEL, REMOVE_EMAIL_CHANNEL, ADD_PAGERDUTY_CHANNEL,
  REMOVE_PAGERDUTY_CHANNEL, ADD_OPSGENIE_CHANNEL, REMOVE_OPSGENIE_CHANNEL,
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
      parentId: payload.parentId,
      repoName: payload.repoName,
      monitorRepo: payload.monitorRepo,
    },
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
      parentId: payload.parentId,
      name: payload.name,
      exporterURL: payload.exporterURL,
      monitorSystem: payload.monitorSystem,
    },
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
      parentId: payload.parentId,
      kmsName: payload.kmsName,
      exporterURL: payload.exporterURL,
      monitorKMS: payload.monitorKMS,
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
