import {
  ADD_CHAIN_SUBSTRATE,
  ADD_NODE_SUBSTRATE,
  REMOVE_NODE_SUBSTRATE,
  TOGGLE_NODE_MONITORING_SUBSTRATE,
  LOAD_CONFIG_SUBSTRATE,
  RESET_CHAIN_SUBSTRATE,
  UPDATE_CHAIN_NAME_SUBSTRATE,
  REMOVE_CHAIN_SUBSTRATE,
  LOAD_REPEAT_ALERTS_SUBSTRATE,
  LOAD_TIMEWINDOW_ALERTS_SUBSTRATE,
  LOAD_THRESHOLD_ALERTS_SUBSTRATE,
  LOAD_SEVERITY_ALERTS_SUBSTRATE,
} from './types';

const { v4: uuidv4 } = require('uuid');

// Only on the creation of a new chain, do you need to assign it
// a new identifier, from then on you re-use the old one.
// When creating a new chain, we must add empty lists as we need to initialise
// the key/value pairs beforehand.
export function addChainSubstrate(payload) {
  let id = `chain_name_${uuidv4()}`;
  if ('id' in payload) {
    id = payload.id;
  }
  return {
    type: ADD_CHAIN_SUBSTRATE,
    payload: {
      id,
      chain_name: payload.chain_name,
    },
  };
}

// This is used to delete the entire configuration of a setup substrate chain
// To be invoked AFTER clearing the actual objects that are referenced in this
// object.
export function removeChainSubstrate(payload) {
  return {
    type: REMOVE_CHAIN_SUBSTRATE,
    payload,
  };
}

// This function is used to change the name of the current chain
export function updateChainSubstrate(payload) {
  return {
    type: UPDATE_CHAIN_NAME_SUBSTRATE,
    payload,
  };
}

// This action is used to reset the current chain name to nothing
// most likely this will happen when click back after setting chain name
// or finishing a configuration setup of a chain
export function resetCurrentChainIdSubstrate() {
  return {
    type: RESET_CHAIN_SUBSTRATE,
  };
}

// Action to add a substrate node to a configuration, payload is intercepted,
// and a unique id is generated for it.
export function addNodeSubstrate(payload) {
  // Generate a unique id for the repository
  let id = `node_${uuidv4()}`;

  // If an ID already exists in the payload use it
  if ('id' in payload) {
    id = payload.id;
  }

  return {
    type: ADD_NODE_SUBSTRATE,
    payload: {
      id,
      parent_id: payload.parent_id,
      name: payload.name,
      node_ws_url: payload.node_ws_url,
      exporter_url: payload.exporter_url,
      monitor_system: payload.monitor_system,
      is_validator: payload.is_validator,
      monitor_node: payload.monitor_node,
      is_archive_node: payload.is_archive_node,
      use_as_data_source: payload.use_as_data_source,
      stash_address: payload.stash_address,
      governance_addresses: payload.governance_addresses,
      monitor_network: payload.monitor_network,
    },
  };
}

// Action toggle network monitoring for all nodes on a substrate chain
export function toggleMonitorNetworkNodesSubstrate(payload) {
  return {
    type: TOGGLE_NODE_MONITORING_SUBSTRATE,
    payload,
  };
}

// Action to remove a substrate node from the current configuration
export function removeNodeSubstrate(payload) {
  return {
    type: REMOVE_NODE_SUBSTRATE,
    payload,
  };
}

export function loadConfigSubstrate(payload) {
  return {
    type: LOAD_CONFIG_SUBSTRATE,
    payload,
  };
}

export function loadRepeatAlertsSubstrate(payload) {
  return {
    type: LOAD_REPEAT_ALERTS_SUBSTRATE,
    payload,
  };
}

export function loadTimeWindowAlertsSubstrate(payload) {
  return {
    type: LOAD_TIMEWINDOW_ALERTS_SUBSTRATE,
    payload,
  };
}

export function loadThresholdAlertsSubstrate(payload) {
  return {
    type: LOAD_THRESHOLD_ALERTS_SUBSTRATE,
    payload,
  };
}

export function loadSeverityAlertsSubstrate(payload) {
  return {
    type: LOAD_SEVERITY_ALERTS_SUBSTRATE,
    payload,
  };
}
