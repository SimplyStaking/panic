import {
  UPDATE_PERIODIC, ADD_REPOSITORY, ADD_SYSTEM, REMOVE_REPOSITORY,
  REMOVE_SYSTEM,
} from '../actions/types';

const initialstate = {
  periodic: {
    time: 0,
    enabled: false,
  },
  systems: [],
  repositories: [],
};

function generalReducer(state = initialstate, action) {
  switch (action.type) {
    case UPDATE_PERIODIC:
      return {
        ...state,
        periodic: action.payload,
      };
    case ADD_REPOSITORY:
      return {
        ...state,
        repositories: state.repositories.concat(action.payload),
      };
    case REMOVE_REPOSITORY:
      return {
        ...state,
        repositories: state.repositories.filter(
          (repository) => repository !== action.payload,
        ),
      };
    case ADD_SYSTEM:
      return {
        ...state,
        systems: state.systems.concat(action.payload),
      };
    case REMOVE_SYSTEM:
      return {
        ...state,
        systems: state.systems.filter((system) => system !== action.payload),
      };
    default:
      return state;
  }
}

export default generalReducer;
