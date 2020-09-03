import {
  ADD_TELEGRAM,
  REMOVE_TELEGRAM,
  ADD_TWILIO,
  REMOVE_TWILIO,
  ADD_EMAIL,
  REMOVE_EMAIL,
} from '../actions/types';

const initialstate = {
  telegrams: [],
  twilios: [],
  emails: [],
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
    case ADD_EMAIL:
      return {
        ...state,
        emails: state.emails.concat(action.payload),
      };
    case REMOVE_EMAIL:
      return {
        ...state,
        emails: state.emails.filter((email) => email !== action.payload),
      };
    default:
      return state;
  }
}

export default channelsReducer;
