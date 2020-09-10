/*
  Reference to understand this reducer code
  https://redux.js.org/recipes/structuring-reducers/refactoring-reducer-example
*/

import { ADD_CHAIN, ADD_NODE } from '../actions/types';

const initialstate = {
  cosmosConfigs: [],
  config: {
    chainName: '',
    nodes: [],
    repositories: [],
    kms: [],
    channels: [],
    alertsThreshold: [],
    alertsSeverity: [],
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
    default:
      return state;
  }
}

export default chainsReducer;
