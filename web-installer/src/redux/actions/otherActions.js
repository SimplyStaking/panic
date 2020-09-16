import {
  UPDATE_PERIODIC,
} from './types';

export default function updatePeriodic(payload) {
  return {
    type: UPDATE_PERIODIC,
    payload,
  };
}
