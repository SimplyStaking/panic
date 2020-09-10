import { CHANGE_PAGE, CHANGE_STEP } from '../actions/types';
import { WELCOME_PAGE, CHAINS_STEP } from '../../constants/constants';

const initialstate = {
  page: WELCOME_PAGE,
  step: CHAINS_STEP,
};

function changePageReducer(state = initialstate, action) {
  switch (action.type) {
    case CHANGE_PAGE:
      return action.payload;
    case CHANGE_STEP:
      return action.paylaod;
    default:
      return state;
  }
}

export default changePageReducer;
