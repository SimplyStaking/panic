import {
  ADD_CHAIN_SUBSTRATE, ADD_NODE_SUBSTRATE, REMOVE_NODE_SUBSTRATE,
  LOAD_CONFIG_SUBSTRATE, RESET_CHAIN_SUBSTRATE, UPDATE_CHAIN_NAME,
  REMOVE_CHAIN_SUBSTRATE, LOAD_NODE_SUBSTRATE, LOAD_REPOSITORY_SUBSTRATE,
  LOAD_REPEAT_ALERTS_SUBSTRATE, LOAD_TIMEWINDOW_ALERTS_SUBSTRATE,
  LOAD_THRESHOLD_ALERTS_SUBSTRATE, LOAD_SEVERITY_ALERTS_SUBSTRATE,
} from './types';

const { v4: uuidv4 } = require('uuid');

// Only on the creation of a new chain, do you need to assign it
// a new identifer, from then on you re-used the old one.
// When creating a new chain, we must add empty lists as we need to intialize
// the key/value pairs beforehand.
export function addChainSubstrate(payload) {
  return {
    type: ADD_CHAIN_SUBSTRATE,
    payload: {
      id: `chain_name_${uuidv4()}`,
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
    type: UPDATE_CHAIN_NAME,
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
// and a unqiue id is generated for it.
export function addNodeSubstrate(payload) {
  return {
    type: ADD_NODE_SUBSTRATE,
    payload: {
      id: `node_${uuidv4()}`,
      parent_id: payload.parent_id,
      substrate_node_name: payload.substrate_node_name,
      node_ws_url: payload.node_ws_url,
      telemetry_url: payload.telemetry_url,
      prometheus_url: payload.prometheus_url,
      exporter_url: payload.exporter_url,
      stash_address: payload.stash_address,
      is_validator: payload.is_validator,
      monitor_node: payload.monitor_node,
      is_archive_node: payload.is_archive_node,
      use_as_data_source: payload.use_as_data_source,
    },
  };
}

export function loadNodeSubstrate(payload) {
  return {
    type: LOAD_NODE_SUBSTRATE,
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

export function loadReposSubstrate(payload) {
  return {
    type: LOAD_REPOSITORY_SUBSTRATE,
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
