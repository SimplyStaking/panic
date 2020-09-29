import { LOGIN, LOGOUT, SET_AUTHENTICATED } from './types';

export function login(payload) {
  return {
    type: LOGIN,
    payload,
  };
}

export function logout(payload) {
  return {
    type: LOGOUT,
    payload,
  };
}

export function setAuthenticated(payload) {
  return {
    type: SET_AUTHENTICATED,
    payload,
  };
}
