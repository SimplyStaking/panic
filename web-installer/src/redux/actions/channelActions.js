import { ADD_TELEGRAM, REMOVE_TELEGRAM } from './types';

export function addTelegram(payload) {
  return {
    type: ADD_TELEGRAM,
    payload,
  };
}

export function removeTelegram(payload) {
  return {
    type: REMOVE_TELEGRAM,
    payload,
  };
}
