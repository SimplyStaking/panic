import {
  UPDATE_PERIODIC, ADD_REPOSITORY, ADD_SYSTEM, REMOVE_REPOSITORY, REMOVE_SYSTEM,
} from './types';

export function updatePeriodic(payload) {
  return {
    type: UPDATE_PERIODIC,
    payload,
  };
}

export function addRepository(payload) {
  return {
    type: ADD_REPOSITORY,
    payload,
  };
}

export function addSystem(payload) {
  return {
    type: ADD_SYSTEM,
    payload,
  };
}

export function removeRepository(payload) {
  return {
    type: REMOVE_REPOSITORY,
    payload,
  };
}

export function removeSystem(payload) {
  return {
    type: REMOVE_SYSTEM,
    payload,
  };
}
