import { CHAINS_STEP } from 'constants/constants';
import { TOGGLE_DIRTY, CHANGE_STEP } from '../actions/types';

const initialstate = {
  step: CHAINS_STEP,
  dirty: false,
};

function changeStepReducer(state = initialstate, action) {
  switch (action.type) {
    case CHANGE_STEP:
      return {
        ...state,
        dirty: false,
        step: action.payload.step,
      };
    case TOGGLE_DIRTY:
      return {
        ...state,
        dirty: action.payload.isDirty,
      };
    default:
      return state;
  }
}

export default changeStepReducer;
