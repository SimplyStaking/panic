/*
  Reference to understand this reducer code
  https://redux.js.org/recipes/structuring-reducers/refactoring-reducer-example
*/

import {
  ADD_CHAIN, ADD_NODE, ADD_REPOSITORY, REMOVE_NODE, REMOVE_REPOSITORY,
  ADD_KMS, REMOVE_KMS, ADD_CHANNEL, REMOVE_CHANNEL, SET_ALERTS,
  ADD_CONFIG, REMOVE_CONFIG,
} from '../actions/types';

const initialstate = {
  cosmosConfigs: [],
  config: {
    chainName: '',
    nodes: [],
    repositories: [],
    kmses: [],
    channels: [],
    alerts: '',
  },
};

function chainsReducer(state = initialstate, action) {
  switch (action.type) {
    case ADD_CHAIN:
      return {
        ...state,
        config: {
          ...state.config,
          chainName: action.payload.chainName,
        },
      };
    case ADD_NODE:
      return {
        ...state,
        config: {
          ...state.config,
          nodes: state.config.nodes.concat(action.payload),
        },
      };
    case REMOVE_NODE:
      return {
        ...state,
        config: {
          ...state.config,
          nodes: state.config.nodes.filter((node) => node !== action.payload),
        },
      };
    case ADD_REPOSITORY:
      return {
        ...state,
        config: {
          ...state.config,
          repositories: state.config.repositories.concat(action.payload),
        },
      };
    case REMOVE_REPOSITORY:
      return {
        ...state,
        config: {
          ...state.config,
          repositories: state.config.repositories.filter(
            (repository) => repository !== action.payload,
          ),
        },
      };
    case ADD_KMS:
      return {
        ...state,
        config: {
          ...state.config,
          kmses: state.config.kmses.concat(action.payload),
        },
      };
    case REMOVE_KMS:
      return {
        ...state,
        config: {
          ...state.config,
          kmses: state.config.kmses.filter(
            (kms) => kms !== action.payload,
          ),
        },
      };
    case ADD_CHANNEL:
      return {
        ...state,
        config: {
          ...state.config,
          channels: state.config.channels.concat(action.payload),
        },
      };
    case REMOVE_CHANNEL:
      return {
        ...state,
        config: {
          ...state.config,
          channels: state.config.channels.filter(
            (channel) => channel !== action.payload,
          ),
        },
      };
    case SET_ALERTS:
      return {
        ...state,
        config: {
          ...state.config,
          alerts: action.payload.alerts,
        },
      };
    case ADD_CONFIG:
      return {
        ...state,
        cosmosConfigs: state.cosmosConfigs.concat(action.payload),
      };
    case REMOVE_CONFIG:
      return {
        ...state,
        cosmosConfigs: state.cosmosConfigs.filter(
          (cosmosConfig) => cosmosConfig !== action.payload,
        ),
      };
    default:
      return state;
  }
}

export default chainsReducer;
