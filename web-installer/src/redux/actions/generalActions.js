import {
  UPDATE_PERIODIC,
  ADD_REPOSITORY,
  ADD_SYSTEM,
  REMOVE_REPOSITORY,
  REMOVE_SYSTEM,
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
  LOAD_THRESHOLD_ALERTS_GENERAL,
  ADD_DOCKER,
  LOAD_DOCKER,
  REMOVE_DOCKER,
  ADD_SLACK_CHANNEL,
  REMOVE_SLACK_CHANNEL,
} from './types';

const { v4: uuidv4 } = require('uuid');

export function updatePeriodic(payload) {
  return {
    type: UPDATE_PERIODIC,
    payload,
  };
}

export function addRepository(payload) {
  // Generate a unique id for the repository
  let id = `repo_${uuidv4()}`;

  // If an ID already exists in the payload use it
  if ('id' in payload) {
    id = payload.id;
  }

  return {
    type: ADD_REPOSITORY,
    payload: {
      id,
      parent_id: payload.parent_id,
      repo_name: payload.repo_name,
      monitor_repo: payload.monitor_repo,
    },
  };
}

export function removeRepository(payload) {
  return {
    type: REMOVE_REPOSITORY,
    payload,
  };
}

export function addDockerHub(payload) {
  // Generate a unique id for the repository
  let id = `docker_${uuidv4()}`;

  // If an ID already exists in the payload use it
  if ('id' in payload) {
    id = payload.id;
  }

  return {
    type: ADD_DOCKER,
    payload: {
      id,
      parent_id: payload.parent_id,
      repo_name: payload.repo_name,
      repo_namespace: payload.repo_namespace,
      monitor_repo: payload.monitor_repo,
    },
  };
}

export function loadDockerHub(payload) {
  return {
    type: LOAD_DOCKER,
    payload,
  };
}

export function removeDockerHub(payload) {
  return {
    type: REMOVE_DOCKER,
    payload,
  };
}

export function addSystem(payload) {
  // Generate a unique id for the repository
  let id = `system_${uuidv4()}`;

  // If an ID already exists in the payload use it
  if ('id' in payload) {
    id = payload.id;
  }

  return {
    type: ADD_SYSTEM,
    payload: {
      id,
      parent_id: payload.parent_id,
      name: payload.name,
      exporter_url: payload.exporter_url,
      monitor_system: payload.monitor_system,
    },
  };
}

export function removeSystem(payload) {
  return {
    type: REMOVE_SYSTEM,
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

export function addSlackChannel(payload) {
  return {
    type: ADD_SLACK_CHANNEL,
    payload,
  };
}

export function removeSlackChannel(payload) {
  return {
    type: REMOVE_SLACK_CHANNEL,
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

export function loadThresholdAlertsGeneral(payload) {
  return {
    type: LOAD_THRESHOLD_ALERTS_GENERAL,
    payload,
  };
}
