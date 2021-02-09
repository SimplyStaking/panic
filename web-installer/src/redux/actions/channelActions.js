import {
  ADD_TELEGRAM,
  REMOVE_TELEGRAM,
  ADD_TWILIO,
  REMOVE_TWILIO,
  ADD_EMAIL,
  REMOVE_EMAIL,
  ADD_PAGERDUTY,
  REMOVE_PAGERDUTY,
  ADD_OPSGENIE,
  REMOVE_OPSGENIE,
  LOAD_TELEGRAM,
  LOAD_TWILIO,
  LOAD_EMAIL,
  LOAD_PAGERDUTY,
  LOAD_OPSGENIE,
} from './types';

const { v4: uuidv4 } = require('uuid');

export function addTelegram(payload) {
  return {
    type: ADD_TELEGRAM,
    payload: {
      id: `telegram_${uuidv4()}`,
      channel_name: payload.channel_name,
      bot_token: payload.bot_token,
      chat_id: payload.chat_id,
      info: payload.info,
      warning: payload.warning,
      critical: payload.critical,
      error: payload.error,
      alerts: payload.alerts,
      commands: payload.commands,
      parent_ids: [],
      parent_names: [],
    },
  };
}

export function loadTelegram(payload) {
  return {
    type: LOAD_TELEGRAM,
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
    payload: {
      id: `twilio_${uuidv4()}`,
      channel_name: payload.channel_name,
      account_sid: payload.account_sid,
      auth_token: payload.auth_token,
      twilio_phone_no: payload.twilio_phone_no,
      twilio_phone_numbers_to_dial_valid: payload.twilio_phone_numbers_to_dial_valid,
      parent_ids: [],
      parent_names: [],
    },
  };
}

export function loadTwilio(payload) {
  return {
    type: LOAD_TWILIO,
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
    payload: {
      id: `email_${uuidv4()}`,
      channel_name: payload.channel_name,
      port: payload.port,
      smtp: payload.smtp,
      email_from: payload.email_from,
      emails_to: payload.emails_to,
      username: payload.username,
      password: payload.password,
      info: payload.info,
      warning: payload.warning,
      critical: payload.critical,
      error: payload.error,
      parent_ids: [],
      parent_names: [],
    },
  };
}

export function loadEmail(payload) {
  return {
    type: LOAD_EMAIL,
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
    payload: {
      id: `pagerduty_${uuidv4()}`,
      channel_name: payload.channel_name,
      api_token: payload.api_token,
      integration_key: payload.integration_key,
      info: payload.info,
      warning: payload.warning,
      critical: payload.critical,
      error: payload.error,
      parent_ids: [],
      parent_names: [],
    },
  };
}

export function loadPagerduty(payload) {
  return {
    type: LOAD_PAGERDUTY,
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
    payload: {
      id: `opsgenie_${uuidv4()}`,
      channel_name: payload.channel_name,
      api_token: payload.api_token,
      eu: payload.eu,
      info: payload.info,
      warning: payload.warning,
      critical: payload.critical,
      error: payload.error,
      parent_ids: [],
      parent_names: [],
    },
  };
}

export function loadOpsgenie(payload) {
  return {
    type: LOAD_OPSGENIE,
    payload,
  };
}

export function removeOpsGenie(payload) {
  return {
    type: REMOVE_OPSGENIE,
    payload,
  };
}
