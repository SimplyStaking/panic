import _ from 'lodash';
import { combineReducers } from 'redux';
import {
  UPDATE_PERIODIC, ADD_REPOSITORY, ADD_SYSTEM, REMOVE_REPOSITORY,
  REMOVE_SYSTEM, ADD_KMS, REMOVE_KMS,
} from '../actions/types';

// Initial periodic state
const periodicState = {
  periodic: {
    time: 0,
    enabled: false,
  },
};

// Periodic alive reminder reducer
function periodicReducer(state = periodicState, action) {
  switch (action.type) {
    case UPDATE_PERIODIC:
      return action.payload;
    default:
      return state;
  }
}

// Reducers to add and remove repository configurations from global state
function repositoriesById(state = {}, action) {
  switch (action.type) {
    case ADD_REPOSITORY:
      return {
        ...state,
        [action.payload.id]: action.payload,
      };
    case REMOVE_REPOSITORY:
      return _.omit(state, action.payload.id);
    default:
      return state;
  }
}

// Reducers to remove from list of all repositories
function allRepositories(state = [], action) {
  switch (action.type) {
    case ADD_REPOSITORY:
      return state.concat(action.payload.id);
    case REMOVE_REPOSITORY:
      return state.filter((config) => config !== action.payload.id);
    default:
      return state;
  }
}

const RepositoryReducer = combineReducers({
  byId: repositoriesById,
  allIds: allRepositories,
});

// Reducers to add and remove system configurations from global state
function systemsById(state = {}, action) {
  switch (action.type) {
    case ADD_SYSTEM:
      return {
        ...state,
        [action.payload.id]: action.payload,
      };
    case REMOVE_SYSTEM:
      return _.omit(state, action.payload.id);
    default:
      return state;
  }
}

// Reducers to remove from list of all systems
function allSystems(state = [], action) {
  switch (action.type) {
    case ADD_SYSTEM:
      return state.concat(action.payload.id);
    case REMOVE_SYSTEM:
      return state.filter((config) => config !== action.payload.id);
    default:
      return state;
  }
}

const SystemsReducer = combineReducers({
  byId: systemsById,
  allIds: allSystems,
});

// Reducers to add and remove kms configurations from global state
function kmsesById(state = {}, action) {
  switch (action.type) {
    case ADD_KMS:
      return {
        ...state,
        [action.payload.id]: action.payload,
      };
    case REMOVE_KMS:
      return _.omit(state, action.payload.id);
    default:
      return state;
  }
}

// Reducers to add and remove from list of all kmses
function allKmses(state = [], action) {
  switch (action.type) {
    case ADD_KMS:
      return state.concat(action.payload.id);
    case REMOVE_KMS:
      return state.filter((config) => config !== action.payload.id);
    default:
      return state;
  }
}

const KmsReducer = combineReducers({
  byId: kmsesById,
  allIds: allKmses,
});
// OLD REDUCER TO BE @REMOVED

// function generalReducer(state = initialstate, action) {
//   switch (action.type) {
//     case UPDATE_PERIODIC:
//       return {
//         ...state,
//         periodic: action.payload,
//       };
//     case ADD_REPOSITORY:
//       return {
//         ...state,
//         repositories: state.repositories.concat(action.payload),
//       };
//     case REMOVE_REPOSITORY:
//       return {
//         ...state,
//         repositories: state.repositories.filter(
//           (repository) => repository !== action.payload,
//         ),
//       };
//     case ADD_SYSTEM:
//       return {
//         ...state,
//         systems: state.systems.concat(action.payload),
//       };
//     case REMOVE_SYSTEM:
//       return {
//         ...state,
//         systems: state.systems.filter((system) => system !== action.payload),
//       };
//     default:
//       return state;
//   }
// }

export {
  RepositoryReducer, SystemsReducer, KmsReducer, periodicReducer,
};
