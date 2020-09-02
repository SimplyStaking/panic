import { ADD_TELEGRAM, REMOVE_TELEGRAM } from '../actions/types';

const initialstate = {
  telegrams: [],
};

function channelsReducer(state = initialstate, action) {
  switch (action.type) {
    case ADD_TELEGRAM:
      return {
        ...state,
        telegrams: state.telegrams.concat(action.payload),
      };
    case REMOVE_TELEGRAM:
      console.log(action.payload);
      return {
        ...state,
        telegrams: state.telegrams.filter((telegram) => telegram !== action.payload),
      };
    default:
      return state;
  }
}

export default channelsReducer;
