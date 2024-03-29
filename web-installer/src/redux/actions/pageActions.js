import {
  CHANGE_PAGE,
  CHANGE_STEP,
  TOGGLE_DIRTY,
  RESET_DIRTY,
} from './types';

export function changePage(payload) {
  return {
    type: CHANGE_PAGE,
    payload,
  };
}

export function changeStep(payload) {
  return {
    type: CHANGE_STEP,
    payload,
  };
}

export function toggleDirty(payload) {
  return {
    type: TOGGLE_DIRTY,
    payload,
  };
}

export function resetDirty() {
  return {
    type: RESET_DIRTY,
  };
}
