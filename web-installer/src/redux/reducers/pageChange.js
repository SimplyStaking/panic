import { WELCOME_PAGE } from 'constants/constants';
import { TOGGLE_DIRTY, CHANGE_PAGE, RESET_DIRTY } from '../actions/types';

const initialstate = {
  page: WELCOME_PAGE,
  dirty: false,
};

function changePageReducer(state = initialstate, action) {
  switch (action.type) {
    case CHANGE_PAGE:
      return {
        ...state,
        dirty: false,
        page: action.payload.page,
      };
    case TOGGLE_DIRTY:
      return {
        ...state,
        dirty: action.payload.isDirty,
      };
    case RESET_DIRTY:
      return {
        ...state,
        dirty: false,
      };
    default:
      return state;
  }
}

export default changePageReducer;
