import { UPDATE_PERIODIC } from '../actions/types';

const initialstate = {
  periodic: 0,
  enabled: false,
};

function changePageReducer(state = initialstate, action) {
  switch (action.type) {
    case UPDATE_PERIODIC:
      return action.payload;
    default:
      return state;
  }
}

export default changePageReducer;
