import {
  ADD_USER, REMOVE_USER
} from 'redux/actions/types';

const initialstate = {
  users: [],
};

function usersReducer(state = initialstate, action) {
  switch (action.type) {
    case ADD_USER:
      return {
        ...state,
        users: state.users.concat(action.payload),
      };
    case REMOVE_USER:
      return {
        ...state,
        users: state.users.filter((username) => username !== action.payload),
      };
    default:
      return state;
  }
}

export default usersReducer;
