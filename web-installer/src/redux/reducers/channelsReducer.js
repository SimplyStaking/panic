import { ADD_TELEGRAM } from '../actions/types';

const initialstate = {
  telegrams: [],
};

function channelsReducer(state = initialstate, action) {
  switch (action.type) {
    case ADD_TELEGRAM:
      return {
        ...state,
        telegrams: state.telegrams.concat(action.payload)
      }
    default:
      return state;
  }
}

export default channelsReducer;
