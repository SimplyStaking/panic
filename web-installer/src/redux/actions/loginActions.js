import { LOGIN, LOGOUT } from './types';

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
