import {
  ADD_CHAIN_CHAINLINK,
  ADD_NODE_CHAINLINK,
  REMOVE_NODE_CHAINLINK,
  LOAD_CONFIG_CHAINLINK,
  RESET_CHAIN_CHAINLINK,
  UPDATE_CHAIN_NAME_CHAINLINK,
  REMOVE_CHAIN_CHAINLINK,
  LOAD_REPEAT_ALERTS_CHAINLINK,
  LOAD_TIMEWINDOW_ALERTS_CHAINLINK,
  LOAD_THRESHOLD_ALERTS_CHAINLINK,
  LOAD_SEVERITY_ALERTS_CHAINLINK,
} from './types';

const { v4: uuidv4 } = require('uuid');

// Only on the creation of a new chain, do you need to assign it
// a new identifier, from then on you re-used the old one.
// When creating a new chain, we must add empty lists as we need to initialise
// the key/value pairs beforehand.
export function addChainChainlink(payload) {
  let id = `chain_name_${uuidv4()}`;
  if ('id' in payload) {
    id = payload.id;
  }
  return {
    type: ADD_CHAIN_CHAINLINK,
    payload: {
      id,
      chain_name: payload.chain_name,
    },
  };
}

// This is used to delete the entire configuration of a setup chainlink chain
// To be invoked AFTER clearing the actual objects that are referenced in this
// object.
export function removeChainChainlink(payload) {
  return {
    type: REMOVE_CHAIN_CHAINLINK,
    payload,
  };
}

// This function is used to change the name of the current chain
export function updateChainChainlink(payload) {
  return {
    type: UPDATE_CHAIN_NAME_CHAINLINK,
    payload,
  };
}

// This action is used to reset the current chain name to nothing
// most likely this will happen when click back after setting chain name
// or finishing a configuration setup of a chain
export function resetCurrentChainIdChainlink() {
  return {
    type: RESET_CHAIN_CHAINLINK,
  };
}

// Action to add a chainlink node to a configuration, payload is intercepted,
// and a unique id is generated for it.
export function addNodeChainlink(payload) {
  let id = `node_${uuidv4()}`;
  if ('id' in payload) {
    id = payload.id;
  }
  return {
    type: ADD_NODE_CHAINLINK,
    payload: {
      id,
      parent_id: payload.parent_id,
      name: payload.name,
      prometheus_url: payload.prometheus_url,
      geth_prometheus_url: payload.geth_prometheus_url,
      monitor_prometheus: payload.monitor_prometheus,
      monitor_geth_prometheus: payload.monitor_geth_prometheus,
      monitor_node: payload.monitor_node,
    },
  };
}

// Action to remove a chainlink node from the current configuration
export function removeNodeChainlink(payload) {
  return {
    type: REMOVE_NODE_CHAINLINK,
    payload,
  };
}

export function loadConfigChainlink(payload) {
  return {
    type: LOAD_CONFIG_CHAINLINK,
    payload,
  };
}

export function loadRepeatAlertsChainlink(payload) {
  return {
    type: LOAD_REPEAT_ALERTS_CHAINLINK,
    payload,
  };
}

export function loadTimeWindowAlertsChainlink(payload) {
  return {
    type: LOAD_TIMEWINDOW_ALERTS_CHAINLINK,
    payload,
  };
}

export function loadThresholdAlertsChainlink(payload) {
  return {
    type: LOAD_THRESHOLD_ALERTS_CHAINLINK,
    payload,
  };
}

export function loadSeverityAlertsChainlink(payload) {
  return {
    type: LOAD_SEVERITY_ALERTS_CHAINLINK,
    payload,
  };
}
