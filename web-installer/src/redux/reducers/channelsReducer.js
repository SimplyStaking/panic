import {
  ADD_TELEGRAM,
  REMOVE_TELEGRAM,
  ADD_TWILIO,
  REMOVE_TWILIO,
} from '../actions/types';

const initialstate = {
  telegrams: [],
  twilios: [],
};

function channelsReducer(state = initialstate, action) {
  switch (action.type) {
    case ADD_TELEGRAM:
      return {
        ...state,
        telegrams: state.telegrams.concat(action.payload),
      };
    case REMOVE_TELEGRAM:
      return {
        ...state,
        telegrams: state.telegrams.filter((telegram) => telegram !== action.payload),
      };
    case ADD_TWILIO:
      return {
        ...state,
        twilios: state.twilios.concat(action.payload),
      };
    case REMOVE_TWILIO:
      return {
        ...state,
        twilios: state.twilios.filter((twilio) => twilio !== action.payload),
      };
    default:
      return state;
  }
}

export default channelsReducer;
