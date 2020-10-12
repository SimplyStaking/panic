import { ADD_USER, REMOVE_USER } from './types';

export function addUser(payload) {
  return {
    type: ADD_USER,
    payload,
  };
}

export function removeUser(payload) {
  return {
    type: REMOVE_USER,
    payload,
  };
}
