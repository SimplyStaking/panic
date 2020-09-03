import {
  ADD_TELEGRAM,
  REMOVE_TELEGRAM,
  ADD_TWILIO,
  REMOVE_TWILIO,
  ADD_EMAIL,
  REMOVE_EMAIL,
} from './types';

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

export function addTwilio(payload) {
  return {
    type: ADD_TWILIO,
    payload,
  };
}

export function removeTwilio(payload) {
  return {
    type: REMOVE_TWILIO,
    payload,
  };
}

export function addEmail(payload) {
  return {
    type: ADD_EMAIL,
    payload,
  };
}

export function removeEmail(payload) {
  return {
    type: REMOVE_EMAIL,
    payload,
  };
}
