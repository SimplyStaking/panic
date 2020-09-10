/*
  Reference to understand this reducer code
  https://redux.js.org/recipes/structuring-reducers/refactoring-reducer-example
*/

import { ADD_CHAIN, REMOVE_CHAIN, ADD_NODE } from '../actions/types';

const initialstate = {
  cosmosChains: [],
};

function chainsReducer(state = initialstate, action) {
  switch (action.type) {
    case ADD_CHAIN:
      return {
        ...state,
        cosmosChains: state.cosmosChains.concat({
          id: action.id,
          chainName: action.chainName,
          nodes: [],
          repositories: [],
          kms: [],
          channels: [],
          alertsThreshold: [],
          alertsSeverity: [],
        }),
      };
    case REMOVE_CHAIN:
      return {
        ...state,
        cosmosChains: state.cosmosChains.filter((cosmosChain) => cosmosChain !== action.payload),
      };
    case ADD_NODE:
      return {
        ...state,
        cosmosChains: state.cosmosChains.map((cosmosChain) => {
          if (cosmosChain.id !== action.id) {
            return cosmosChain;
          }

          return {
            ...cosmosChain,
            nodes: cosmosChain.nodes.concat(action.payload),
          };
        }),
      };
    default:
      return state;
  }
}

export default chainsReducer;
