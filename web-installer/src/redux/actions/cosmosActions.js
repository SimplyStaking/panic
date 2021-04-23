import {
  ADD_CHAIN_COSMOS,
  ADD_NODE_COSMOS,
  REMOVE_NODE_COSMOS,
  LOAD_CONFIG_COSMOS,
  RESET_CHAIN_COSMOS,
  UPDATE_CHAIN_NAME_COSMOS,
  REMOVE_CHAIN_COSMOS,
  LOAD_REPEAT_ALERTS_COSMOS,
  LOAD_TIMEWINDOW_ALERTS_COSMOS,
  LOAD_THRESHOLD_ALERTS_COSMOS,
  LOAD_SEVERITY_ALERTS_COSMOS,
} from './types';

const { v4: uuidv4 } = require('uuid');

// Only on the creation of a new chain, do you need to assign it
// a new identifier, from then on you re-used the old one.
// When creating a new chain, we must add empty lists as we need to initialise
// the key/value pairs beforehand.
export function addChainCosmos(payload) {
  let id = `chain_name_${uuidv4()}`;
  if ('id' in payload) {
    id = payload.id;
  }
  return {
    type: ADD_CHAIN_COSMOS,
    payload: {
      id,
      chain_name: payload.chain_name,
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
    type: UPDATE_CHAIN_NAME_COSMOS,
    payload,
  };
}

// This action is used to reset the current chain name to nothing
// most likely this will happen when click back after setting chain name
// or finishing a configuration setup of a chain
export function resetCurrentChainIdCosmos() {
  return {
    type: RESET_CHAIN_COSMOS,
  };
}

// Action to add a cosmos node to a configuration, payload is intercepted,
// and a unique id is generated for it.
export function addNodeCosmos(payload) {
  let id = `node_${uuidv4()}`;
  if ('id' in payload) {
    id = payload.id;
  }
  return {
    type: ADD_NODE_COSMOS,
    payload: {
      id,
      parent_id: payload.parent_id,
      name: payload.name,
      tendermint_rpc_url: payload.tendermint_rpc_url,
      monitor_tendermint: payload.monitor_tendermint,
      cosmos_rpc_url: payload.cosmos_rpc_url,
      monitor_rpc: payload.monitor_rpc,
      prometheus_url: payload.prometheus_url,
      monitor_prometheus: payload.monitor_prometheus,
      exporter_url: payload.exporter_url,
      monitor_system: payload.monitor_system,
      is_validator: payload.is_validator,
      monitor_node: payload.monitor_node,
      is_archive_node: payload.is_archive_node,
      use_as_data_source: payload.use_as_data_source,
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

export function loadRepeatAlertsCosmos(payload) {
  return {
    type: LOAD_REPEAT_ALERTS_COSMOS,
    payload,
  };
}

export function loadTimeWindowAlertsCosmos(payload) {
  return {
    type: LOAD_TIMEWINDOW_ALERTS_COSMOS,
    payload,
  };
}

export function loadThresholdAlertsCosmos(payload) {
  return {
    type: LOAD_THRESHOLD_ALERTS_COSMOS,
    payload,
  };
}

export function loadSeverityAlertsCosmos(payload) {
  return {
    type: LOAD_SEVERITY_ALERTS_COSMOS,
    payload,
  };
}
