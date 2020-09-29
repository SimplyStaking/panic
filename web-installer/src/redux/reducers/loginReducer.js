import { LOGIN, LOGOUT, SET_AUTHENTICATED } from '../actions/types';

const initialstate = {
  username: '',
  password: '',
  authenticated: false,
};

function loginReducer(state = initialstate, action) {
  switch (action.type) {
    case LOGIN:
      return {
        ...state,
        username: action.payload.username,
        password: action.payload.password,
      };
    case LOGOUT:
      return initialstate;
    case SET_AUTHENTICATED:
      return {
        ...state,
        authenticated: action.payload,
      };
    default:
      return state;
  }
}

export default loginReducer;
