import { LOGIN, LOGOUT } from '../actions/types';

const initialstate = {
  username: '',
  password: '',
};

function loginReducer(state = initialstate, action) {
  switch (action.type) {
    case LOGIN:
      return action.payload;
    case LOGOUT:
      return initialstate;
    default:
      return state;
  }
}

export default loginReducer;
