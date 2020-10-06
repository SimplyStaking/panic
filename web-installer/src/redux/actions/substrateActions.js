import {
  ADD_CHAIN_SUBSTRATE, ADD_NODE_SUBSTRATE, REMOVE_NODE_SUBSTRATE, LOAD_CONFIG_SUBSTRATE,
  RESET_CHAIN_SUBSTRATE, UPDATE_CHAIN_NAME, REMOVE_CHAIN_SUBSTRATE,
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
      chainName: payload.chainName,
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
export function resetCurrentChainId() {
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
      parentId: payload.parentId,
      substrateNodeName: payload.substrateNodeName,
      nodeWSURL: payload.nodeWSURL,
      telemetryURL: payload.telemetryURL,
      prometheusURL: payload.prometheusURL,
      exporterURL: payload.exporterURL,
      stashAddress: payload.stashAddress,
      isValidator: payload.isValidator,
      monitorNode: payload.monitorNode,
      isArchiveNode: payload.isArchiveNode,
      useAsDataSource: payload.useAsDataSource,
    },
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
