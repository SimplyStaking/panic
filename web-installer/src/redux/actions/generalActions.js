import {
  UPDATE_PERIODIC, ADD_REPOSITORY, ADD_SYSTEM, REMOVE_REPOSITORY, REMOVE_SYSTEM,
  ADD_KMS, REMOVE_KMS,
} from './types';

const { v4: uuidv4 } = require('uuid');

export function updatePeriodic(payload) {
  return {
    type: UPDATE_PERIODIC,
    payload,
  };
}

export function addRepository(payload) {
  return {
    type: ADD_REPOSITORY,
    payload: {
      id: uuidv4(),
      parentId: payload.parentId,
      repoName: payload.repoName,
      monitorRepo: payload.monitorRepo,
    },
  };
}

export function removeRepository(payload) {
  return {
    type: REMOVE_REPOSITORY,
    payload,
  };
}

export function addSystem(payload) {
  return {
    type: ADD_SYSTEM,
    payload: {
      id: uuidv4(),
      parentId: payload.parentId,
      name: payload.name,
      exporterURL: payload.exporterURL,
      enabled: payload.enabled,
    },
  };
}

export function removeSystem(payload) {
  return {
    type: REMOVE_SYSTEM,
    payload,
  };
}

export function addKms(payload) {
  return {
    type: ADD_KMS,
    payload: {
      id: uuidv4(),
      parentId: payload.parentId,
      kmsName: payload.kmsName,
      exporterURL: payload.exporterURL,
      monitorKMS: payload.monitorKMS,
    },
  };
}

export function removeKms(payload) {
  return {
    type: REMOVE_KMS,
    payload,
  };
}
