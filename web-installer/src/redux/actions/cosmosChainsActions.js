import {
  ADD_CHAIN_COSMOS, ADD_NODE_COSMOS, ADD_REPOSITORY_COSMOS, REMOVE_NODE_COSMOS,
  REMOVE_REPOSITORY_COSMOS, ADD_KMS_COSMOS, REMOVE_KMS_COSMOS, SET_ALERTS_COSMOS,
  ADD_CONFIG_COSMOS, REMOVE_CONFIG_COSMOS, RESET_CONFIG_COSMOS,
  LOAD_CONFIG_COSMOS, ADD_TELEGRAM_CHANNEL, REMOVE_TELEGRAM_CHANNEL,
  ADD_TWILIO_CHANNEL, REMOVE_TWILIO_CHANNEL, ADD_EMAIL_CHANNEL,
  REMOVE_EMAIL_CHANNEL, ADD_PAGERDUTY_CHANNEL, REMOVE_PAGERDUTY_CHANNEL,
  ADD_OPSGENIE_CHANNEL, REMOVE_OPSGENIE_CHANNEL, UPDATE_WARNING_DELAY_COSMOS,
  UPDATE_WARNING_REPEAT_COSMOS, UPDATE_WARNING_THRESHOLD_COSMOS,
  UPDATE_WARNING_TIMEWINDOW_COSMOS, UPDATE_WARNING_ENABLED_COSMOS,
  UPDATE_CRITICAL_DELAY_COSMOS, UPDATE_CRITICAL_REPEAT_COSMOS,
  UPDATE_CRITICAL_THRESHOLD_COSMOS, UPDATE_CRITICAL_TIMEWINDOW_COSMOS,
  UPDATE_CRITICAL_ENABLED_COSMOS, UPDATE_ALERT_ENABLED_COSMOS,
  UPDATE_ALERT_SEVERTY_LEVEL_COSMOS, UPDATE_ALERT_SEVERTY_ENABLED_COSMOS,
  RESET_CHAIN_COSMOS, UPDATE_CHAIN_NAME, REMOVE_CHAIN_COSMOS,
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
      nodes: [],
      kmses: [],
      repositories: [],
      alerts: [],
      telegrams: [],
      twilios: [],
      emails: [],
      pagerduties: [],
      opsgenies: [],
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

// @REMOVE Currently edited out, potentially not needed

// This function is used to keep track of which cosmos chain we are currently
// editing in the multi-step form.
// export function setCurrentCosmosChain(payload) {
//   return {
//     type: SET_CHAIN_COSMOS,
//     payload,
//   };
// }

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

// @REMOVE remove the 4 functions underneath, these are now general
export function addRepositoryCosmos(payload) {
  return {
    type: ADD_REPOSITORY_COSMOS,
    payload,
  };
}

export function removeRepositoryCosmos(payload) {
  return {
    type: REMOVE_REPOSITORY_COSMOS,
    payload,
  };
}

export function addKMSCosmos(payload) {
  return {
    type: ADD_KMS_COSMOS,
    payload,
  };
}

export function removeKMSCosmos(payload) {
  return {
    type: REMOVE_KMS_COSMOS,
    payload,
  };
}

export function setAlertsCosmos(payload) {
  return {
    type: SET_ALERTS_COSMOS,
    payload,
  };
}

export function addConfigCosmos() {
  return {
    type: ADD_CONFIG_COSMOS,
  };
}

export function removeConfigCosmos(payload) {
  return {
    type: REMOVE_CONFIG_COSMOS,
    payload,
  };
}

export function resetConfigCosmos() {
  return {
    type: RESET_CONFIG_COSMOS,
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

export function updateWarningDelayCosmos(payload) {
  return {
    type: UPDATE_WARNING_DELAY_COSMOS,
    payload,
  };
}

export function updateWarningRepeatCosmos(payload) {
  return {
    type: UPDATE_WARNING_REPEAT_COSMOS,
    payload,
  };
}

export function updateWarningThresholdCosmos(payload) {
  return {
    type: UPDATE_WARNING_THRESHOLD_COSMOS,
    payload,
  };
}

export function updateWarningTimeWindowCosmos(payload) {
  return {
    type: UPDATE_WARNING_TIMEWINDOW_COSMOS,
    payload,
  };
}

export function updateWarningEnabledCosmos(payload) {
  return {
    type: UPDATE_WARNING_ENABLED_COSMOS,
    payload,
  };
}

export function updateCriticalDelayCosmos(payload) {
  return {
    type: UPDATE_CRITICAL_DELAY_COSMOS,
    payload,
  };
}

export function updateCriticalRepeatCosmos(payload) {
  return {
    type: UPDATE_CRITICAL_REPEAT_COSMOS,
    payload,
  };
}

export function updateCriticalThresholdCosmos(payload) {
  return {
    type: UPDATE_CRITICAL_THRESHOLD_COSMOS,
    payload,
  };
}

export function updateCriticalTimeWindowCosmos(payload) {
  return {
    type: UPDATE_CRITICAL_TIMEWINDOW_COSMOS,
    payload,
  };
}

export function updateCriticalEnabledCosmos(payload) {
  return {
    type: UPDATE_CRITICAL_ENABLED_COSMOS,
    payload,
  };
}

export function updateAlertEnabledCosmos(payload) {
  return {
    type: UPDATE_ALERT_ENABLED_COSMOS,
    payload,
  };
}

export function updateAlertSeverityLevelCosmos(payload) {
  return {
    type: UPDATE_ALERT_SEVERTY_LEVEL_COSMOS,
    payload,
  };
}

export function updateAlertSeverityEnabledCosmos(payload) {
  return {
    type: UPDATE_ALERT_SEVERTY_ENABLED_COSMOS,
    payload,
  };
}
