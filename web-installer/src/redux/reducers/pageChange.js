import { CHANGE_PAGE } from '../actions/types';
import { WELCOME_PAGE } from 'constants/constants';

const initialstate = {
  page: WELCOME_PAGE,
};

function changePageReducer(state = initialstate, action) {
  switch (action.type) {
    case CHANGE_PAGE:
      return action.payload;
    default:
      return state;
  }
}

export default changePageReducer;
