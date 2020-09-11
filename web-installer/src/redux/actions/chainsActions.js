import {
  ADD_CHAIN, ADD_NODE, ADD_REPOSITORY, REMOVE_NODE, REMOVE_REPOSITORY,
  ADD_KMS, REMOVE_KMS, ADD_CHANNEL, REMOVE_CHANNEL, SET_ALERTS,
  ADD_CONFIG, REMOVE_CONFIG,
} from './types';

export function addChain(payload) {
  return {
    type: ADD_CHAIN,
    payload,
  };
}

export function addNode(payload) {
  return {
    type: ADD_NODE,
    payload,
  };
}

export function removeNode(payload) {
  return {
    type: REMOVE_NODE,
    payload,
  };
}

export function addRepository(payload) {
  return {
    type: ADD_REPOSITORY,
    payload,
  };
}

export function removeRepository(payload) {
  return {
    type: REMOVE_REPOSITORY,
    payload,
  };
}

export function addKMS(payload) {
  return {
    type: ADD_KMS,
    payload,
  };
}

export function removeKMS(payload) {
  return {
    type: REMOVE_KMS,
    payload,
  };
}

export function addChannel(payload) {
  return {
    type: ADD_CHANNEL,
    payload,
  };
}

export function removeChannel(payload) {
  return {
    type: REMOVE_CHANNEL,
    payload,
  };
}

export function setAlerts(payload) {
  return {
    type: SET_ALERTS,
    payload,
  };
}

export function addConfig(payload) {
  return {
    type: ADD_CONFIG,
    payload,
  };
}

export function removeConfig(payload) {
  return {
    type: REMOVE_CONFIG,
    payload,
  };
}
