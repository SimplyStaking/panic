import { ADD_USER, REMOVE_USER } from '../actions/types';

const initialstate = {
  users: [],
};

function changePageReducer(state = initialstate, action) {
  switch (action.type) {
    case ADD_USER:
      return {
        ...state,
        users: state.users.concat(action.payload),
      };
    case REMOVE_USER:
      return {
        ...state,
        users: state.users.filter((user) => user !== action.payload),
      };
    default:
      return state;
  }
}

export default changePageReducer;
