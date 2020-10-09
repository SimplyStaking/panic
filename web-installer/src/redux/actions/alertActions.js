import {
  UPDATE_REPEAT_ALERT, UPDATE_TIMEWINDOW_ALERT,
  UPDATE_THRESHOLD_ALERT, UPDATE_SEVERITY_ALERT,
} from './types';

export function updateRepeatAlert(payload) {
  return {
    type: UPDATE_REPEAT_ALERT,
    payload,
  };
}

export function updateTimeWindowAlert(payload) {
  return {
    type: UPDATE_TIMEWINDOW_ALERT,
    payload,
  };
}

export function updateThresholdAlert(payload) {
  return {
    type: UPDATE_THRESHOLD_ALERT,
    payload,
  };
}

export function updateSeverityAlert(payload) {
  return {
    type: UPDATE_SEVERITY_ALERT,
    payload,
  };
}
