import {
  ADD_CHAIN_COSMOS, ADD_NODE_COSMOS, REMOVE_NODE_COSMOS, LOAD_CONFIG_COSMOS,
  ADD_TELEGRAM_CHANNEL, REMOVE_TELEGRAM_CHANNEL, ADD_TWILIO_CHANNEL,
  REMOVE_TWILIO_CHANNEL, ADD_EMAIL_CHANNEL, REMOVE_EMAIL_CHANNEL,
  ADD_PAGERDUTY_CHANNEL, REMOVE_PAGERDUTY_CHANNEL, ADD_OPSGENIE_CHANNEL,
  REMOVE_OPSGENIE_CHANNEL, RESET_CHAIN_COSMOS, UPDATE_CHAIN_NAME,
  REMOVE_CHAIN_COSMOS, UPDATE_REPEAT_ALERT, UPDATE_TIMEWINDOW_ALERT,
  UPDATE_THRESHOLD_ALERT, UPDATE_SEVERITY_ALERT,
} from './types';

const { v4: uuidv4 } = require('uuid');

// Only on the creation of a new chain, do you need to assign it
// a new identifer, from then on you re-used the old one.
// When creating a new chain, we must add empty lists as we need to intialize
// the key/value pairs beforehand.
export function addChainCosmos(payload) {
  return {
    type: ADD_CHAIN_COSMOS,
    payload: {
      id: uuidv4(),
      chainName: payload.chainName,
    },
  };
}

// This is used to delete the entire configuration of a setup cosmos chain
// To be invoked AFTER clearing the actual objects that are referenced in this
// object.
export function removeChainCosmos(payload) {
  return {
    type: REMOVE_CHAIN_COSMOS,
    payload,
  };
}

// This function is used to change the name of the current chain
export function updateChainCosmos(payload) {
  return {
    type: UPDATE_CHAIN_NAME,
    payload,
  };
}

// This action is used to reset the current chain name to nothing
// most likely this will happen when click back after setting chain name
// or finishing a configuration setup of a chain
export function resetCurrentChainId() {
  return {
    type: RESET_CHAIN_COSMOS,
  };
}

// Action to add a cosmos node to a configuration, payload is intercepted,
// and a unqiue id is generated for it.
export function addNodeCosmos(payload) {
  return {
    type: ADD_NODE_COSMOS,
    payload: {
      id: uuidv4(),
      parentId: payload.parentId,
      cosmosNodeName: payload.cosmosNodeName,
      tendermintRPCURL: payload.tendermintRPCURL,
      cosmosRPCURL: payload.cosmosRPCURL,
      prometheusURL: payload.prometheusURL,
      exporterURL: payload.exporterURL,
      isValidator: payload.isValidator,
      monitorNode: payload.monitorNode,
      isArchiveNode: payload.isArchiveNode,
      useAsDataSource: payload.useAsDataSource,
    },
  };
}

// Action to remove a cosmos node from the current configuration
export function removeNodeCosmos(payload) {
  return {
    type: REMOVE_NODE_COSMOS,
    payload,
  };
}

export function loadConfigCosmos(payload) {
  return {
    type: LOAD_CONFIG_COSMOS,
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

export function updateRepeatAlert(payload) {
  return {
    type: UPDATE_REPEAT_ALERT,
    payload,
  };
}

export function updateTimeWindowAlert(payload) {
  return {
    type: UPDATE_TIMEWINDOW_ALERT,
    payload,
  };
}

export function updateThresholdAlert(payload) {
  return {
    type: UPDATE_THRESHOLD_ALERT,
    payload,
  };
}

export function updateSeverityAlert(payload) {
  return {
    type: UPDATE_SEVERITY_ALERT,
    payload,
  };
}
