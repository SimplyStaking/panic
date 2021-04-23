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
  ADD_SLACK,
  REMOVE_SLACK,
} from './types';

const { v4: uuidv4 } = require('uuid');

export function addSlack(payload) {
  // Generate a unique id for the slack config
  let id = `slack_${uuidv4()}`;

  // If an ID already exists in the payload use it
  if ('id' in payload) {
    id = payload.id;
  }

  return {
    type: ADD_SLACK,
    payload: {
      id,
      channel_name: payload.channel_name,
      token: payload.token,
      chat_id: payload.chat_id,
      info: payload.info,
      warning: payload.warning,
      critical: payload.critical,
      error: payload.error,
      alerts: payload.alerts,
      commands: payload.commands,
      parent_ids: payload.parent_ids,
      parent_names: payload.parent_names,
    },
  };
}

export function removeSlack(payload) {
  return {
    type: REMOVE_SLACK,
    payload,
  };
}

export function addTelegram(payload) {
  // Generate a unique id for the telegram config
  let id = `telegram_${uuidv4()}`;

  // If an ID already exists in the payload use it
  if ('id' in payload) {
    id = payload.id;
  }

  return {
    type: ADD_TELEGRAM,
    payload: {
      id,
      channel_name: payload.channel_name,
      bot_token: payload.bot_token,
      chat_id: payload.chat_id,
      info: payload.info,
      warning: payload.warning,
      critical: payload.critical,
      error: payload.error,
      alerts: payload.alerts,
      commands: payload.commands,
      parent_ids: payload.parent_ids,
      parent_names: payload.parent_names,
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
  // Generate a unique id for the twilio config
  let id = `twilio_${uuidv4()}`;

  // If an ID already exists in the payload use it
  if ('id' in payload) {
    id = payload.id;
  }

  return {
    type: ADD_TWILIO,
    payload: {
      id,
      channel_name: payload.channel_name,
      account_sid: payload.account_sid,
      auth_token: payload.auth_token,
      twilio_phone_no: payload.twilio_phone_no,
      twilio_phone_numbers_to_dial_valid: payload.twilio_phone_numbers_to_dial_valid,
      parent_ids: payload.parent_ids,
      parent_names: payload.parent_names,
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
  // Generate a unique id for the email config
  let id = `email_${uuidv4()}`;

  // If an ID already exists in the payload use it
  if ('id' in payload) {
    id = payload.id;
  }

  return {
    type: ADD_EMAIL,
    payload: {
      id,
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
      parent_ids: payload.parent_ids,
      parent_names: payload.parent_names,
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
  // Generate a unique id for the pagerduty config
  let id = `pagerduty_${uuidv4()}`;

  // If an ID already exists in the payload use it
  if ('id' in payload) {
    id = payload.id;
  }

  return {
    type: ADD_PAGERDUTY,
    payload: {
      id,
      channel_name: payload.channel_name,
      api_token: payload.api_token,
      integration_key: payload.integration_key,
      info: payload.info,
      warning: payload.warning,
      critical: payload.critical,
      error: payload.error,
      parent_ids: payload.parent_ids,
      parent_names: payload.parent_names,
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
  // Generate a unique id for the opsgenie config
  let id = `opsgenie_${uuidv4()}`;

  // If an ID already exists in the payload use it
  if ('id' in payload) {
    id = payload.id;
  }

  return {
    type: ADD_OPSGENIE,
    payload: {
      id,
      channel_name: payload.channel_name,
      api_token: payload.api_token,
      eu: payload.eu,
      info: payload.info,
      warning: payload.warning,
      critical: payload.critical,
      error: payload.error,
      parent_ids: payload.parent_ids,
      parent_names: payload.parent_names,
    },
  };
}

export function removeOpsGenie(payload) {
  return {
    type: REMOVE_OPSGENIE,
    payload,
  };
}
