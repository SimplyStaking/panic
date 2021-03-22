import { CHANGE_PAGE, CHANGE_STEP } from './types';

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
