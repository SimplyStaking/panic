import { CHANGE_STEP } from '../actions/types';
import { CHAINS_STEP } from '../../constants/constants';

const initialstate = {
  step: CHAINS_STEP,
};

function changeStepReducer(state = initialstate, action) {
  switch (action.type) {
    case CHANGE_STEP:
      return action.payload;
    default:
      return state;
  }
}

export default changeStepReducer;
