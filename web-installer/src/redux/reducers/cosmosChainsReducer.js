import _ from 'lodash';
import { combineReducers } from 'redux';
import {
  ADD_CHAIN_COSMOS, ADD_NODE_COSMOS, REMOVE_NODE_COSMOS,
  REMOVE_CHAIN_COSMOS, UPDATE_CHAIN_NAME, RESET_CHAIN_COSMOS,
} from '../actions/types';

// Substrate and Cosmos nodes could be grouped up together, but I think it's
// better to keep them seperate and therefore more manageable. This is because
// unlike KMS/Github they have different keys.

// Reducers to add and remove cosmos node configurations from global state
function nodesById(state = {}, action) {
  switch (action.type) {
    case ADD_NODE_COSMOS:
      return {
        ...state,
        [action.payload.id]: action.payload,
      };
    case REMOVE_NODE_COSMOS:
      return _.omit(state, action.payload.id);
    default:
      return state;
  }
}

// Reducers to add and remove from list of all cosmos nodes
function allNodes(state = [], action) {
  switch (action.type) {
    case ADD_NODE_COSMOS:
      return state.concat(action.payload.id);
    case REMOVE_NODE_COSMOS:
      return state.filter((config) => config !== action.payload.id);
    default:
      return state;
  }
}

const CosmosNodesReducer = combineReducers({
  byId: nodesById,
  allIds: allNodes,
});

function cosmosChainsById(state = {}, action) {
  switch (action.type) {
    case ADD_CHAIN_COSMOS:
      return {
        ...state,
        [action.payload.id]: action.payload,
      };
    case UPDATE_CHAIN_NAME:
      return {
        ...state,
        [action.payload.id]: {
          ...state[action.payload.id],
          chainName: action.payload.chainName,
        },
      };
    case ADD_NODE_COSMOS:
      return {
        ...state,
        [action.payload.id]: {
          ...state[action.payload.id],
          nodes: state[action.payload.id].nodes.concat(action.payload.cosmosNodeName),
        },
      };
    case REMOVE_NODE_COSMOS:
      return {
        ...state,
        [action.payload.id]: {
          ...state[action.payload.id],
          nodes: state[action.payload.id].nodes.filter(
            (config) => config !== action.payload.cosmosNodeName,
          ),
        },
      };
    case REMOVE_CHAIN_COSMOS:
      return _.omit(state, action.payload.id);
    default:
      return state;
  }
}

function allCosmosChains(state = [], action) {
  switch (action.type) {
    case ADD_CHAIN_COSMOS:
      return state.concat(action.payload.id);
    case REMOVE_CHAIN_COSMOS:
      return state.filter((config) => config !== action.payload.id);
    default:
      return state;
  }
}

const CosmosChainsReducer = combineReducers({
  byId: cosmosChainsById,
  allIds: allCosmosChains,
});

function CurrentCosmosChain(state = '', action) {
  switch (action.type) {
    case ADD_CHAIN_COSMOS:
      return action.payload.id;
    case RESET_CHAIN_COSMOS:
      return '';
    default:
      return state;
  }
}
export {
  CosmosNodesReducer, CosmosChainsReducer, CurrentCosmosChain,
};

// OLD Reducer to be removed

// function cosmosChainsReducer(state = {}, action) {
//   switch (action.type) {
//     case ADD_CHAIN_COSMOS:
//       return {
//         ...state,
//         config: {
//           ...state.config,
//           chainName: action.payload.chainName,
//         },
//       };
//     case ADD_REPOSITORY_COSMOS:
//       return {
//         ...state,
//         config: {
//           ...state.config,
//           repositories: state.config.repositories.concat(action.payload),
//         },
//       };
//     case REMOVE_REPOSITORY_COSMOS:
//       return {
//         ...state,
//         config: {
//           ...state.config,
//           repositories: state.config.repositories.filter(
//             (repository) => repository !== action.payload,
//           ),
//         },
//       };
//     case ADD_KMS_COSMOS:
//       return {
//         ...state,
//         config: {
//           ...state.config,
//           kmses: state.config.kmses.concat(action.payload),
//         },
//       };
//     case REMOVE_KMS_COSMOS:
//       return {
//         ...state,
//         config: {
//           ...state.config,
//           kmses: state.config.kmses.filter(
//             (kms) => kms !== action.payload,
//           ),
//         },
//       };
//     case ADD_TELEGRAM_CHANNEL_COSMOS:
//       return {
//         ...state,
//         config: {
//           ...state.config,
//           telegrams: state.config.telegrams.concat(action.payload),
//         },
//       };
//     case REMOVE_TELEGRAM_CHANNEL_COSMOS:
//       return {
//         ...state,
//         config: {
//           ...state.config,
//           telegrams: state.config.telegrams.filter(
//             (telegram) => telegram !== action.payload,
//           ),
//         },
//       };
//     case ADD_OPSGENIE_CHANNEL_COSMOS:
//       return {
//         ...state,
//         config: {
//           ...state.config,
//           opsgenies: state.config.opsgenies.concat(action.payload),
//         },
//       };
//     case REMOVE_OPSGENIE_CHANNEL_COSMOS:
//       return {
//         ...state,
//         config: {
//           ...state.config,
//           opsgenies: state.config.opsgenies.filter(
//             (opsgenie) => opsgenie !== action.payload,
//           ),
//         },
//       };
//     case ADD_EMAIL_CHANNEL_COSMOS:
//       return {
//         ...state,
//         config: {
//           ...state.config,
//           emails: state.config.emails.concat(action.payload),
//         },
//       };
//     case REMOVE_EMAIL_CHANNEL_COSMOS:
//       return {
//         ...state,
//         config: {
//           ...state.config,
//           emails: state.config.emails.filter(
//             (email) => email !== action.payload,
//           ),
//         },
//       };
//     case ADD_TWILIO_CHANNEL_COSMOS:
//       return {
//         ...state,
//         config: {
//           ...state.config,
//           twilios: state.config.twilios.concat(action.payload),
//         },
//       };
//     case REMOVE_TWILIO_CHANNEL_COSMOS:
//       return {
//         ...state,
//         config: {
//           ...state.config,
//           twilios: state.config.twilios.filter(
//             (twilio) => twilio !== action.payload,
//           ),
//         },
//       };
//     case ADD_PAGERDUTY_CHANNEL_COSMOS:
//       return {
//         ...state,
//         config: {
//           ...state.config,
//           pagerduties: state.config.pagerduties.concat(action.payload),
//         },
//       };
//     case REMOVE_PAGERDUTY_CHANNEL_COSMOS:
//       return {
//         ...state,
//         config: {
//           ...state.config,
//           pagerduties: state.config.pagerduties.filter(
//             (pagerduty) => pagerduty !== action.payload,
//           ),
//         },
//       };
//     case SET_ALERTS_COSMOS:
//       return {
//         ...state,
//         config: {
//           ...state.config,
//           alerts: action.payload.alerts,
//         },
//       };
//     case ADD_CONFIG_COSMOS:
//       return {
//         ...state,
//         cosmosConfigs: state.cosmosConfigs.concat(state.config),
//       };
//     case REMOVE_CONFIG_COSMOS:
//       return {
//         ...state,
//         cosmosConfigs: state.cosmosConfigs.filter(
//           (cosmosConfig) => cosmosConfig !== action.payload,
//         ),
//       };
//     case RESET_CONFIG_COSMOS:
//       return {
//         ...state,
//         config: initialstate.config,
//       };
//     case LOAD_CONFIG_COSMOS:
//       return {
//         ...state,
//         config: state.cosmosConfigs.filter(
//           (cosmosConfig) => cosmosConfig === action.payload,
//         )[0],
//       };
//     case UPDATE_WARNING_DELAY_COSMOS:
//       return {
//         ...state,
//         config: {
//           ...state.config,
//           alerts: {
//             ...state.config.alerts,
//             thresholds: {
//               ...state.config.alerts.thresholds,
//               [action.payload.alertID]: {
//                 ...state.config.alerts.thresholds[action.payload.alertID],
//                 warning: {
//                   ...state.config.alerts.thresholds[action.payload.alertID].warning,
//                   delay: action.payload.delay,
//                 },
//               },
//             },
//           },
//         },
//       };
//     case UPDATE_WARNING_REPEAT_COSMOS:
//       return {
//         ...state,
//         config: {
//           ...state.config,
//           alerts: {
//             ...state.config.alerts,
//             thresholds: {
//               ...state.config.alerts.thresholds,
//               [action.payload.alertID]: {
//                 ...state.config.alerts.thresholds[action.payload.alertID],
//                 warning: {
//                   ...state.config.alerts.thresholds[action.payload.alertID].warning,
//                   repeat: action.payload.repeat,
//                 },
//               },
//             },
//           },
//         },
//       };
//     case UPDATE_WARNING_THRESHOLD_COSMOS:
//       return {
//         ...state,
//         config: {
//           ...state.config,
//           alerts: {
//             ...state.config.alerts,
//             thresholds: {
//               ...state.config.alerts.thresholds,
//               [action.payload.alertID]: {
//                 ...state.config.alerts.thresholds[action.payload.alertID],
//                 warning: {
//                   ...state.config.alerts.thresholds[action.payload.alertID].warning,
//                   threshold: action.payload.threshold,
//                 },
//               },
//             },
//           },
//         },
//       };
//     case UPDATE_WARNING_TIMEWINDOW_COSMOS:
//       return {
//         ...state,
//         config: {
//           ...state.config,
//           alerts: {
//             ...state.config.alerts,
//             thresholds: {
//               ...state.config.alerts.thresholds,
//               [action.payload.alertID]: {
//                 ...state.config.alerts.thresholds[action.payload.alertID],
//                 warning: {
//                   ...state.config.alerts.thresholds[action.payload.alertID].warning,
//                   timewindow: action.payload.timewindow,
//                 },
//               },
//             },
//           },
//         },
//       };
//     case UPDATE_WARNING_ENABLED_COSMOS:
//       return {
//         ...state,
//         config: {
//           ...state.config,
//           alerts: {
//             ...state.config.alerts,
//             thresholds: {
//               ...state.config.alerts.thresholds,
//               [action.payload.alertID]: {
//                 ...state.config.alerts.thresholds[action.payload.alertID],
//                 warning: {
//                   ...state.config.alerts.thresholds[action.payload.alertID].warning,
//                   enabled: action.payload.enabled,
//                 },
//               },
//             },
//           },
//         },
//       };
//     case UPDATE_CRITICAL_DELAY_COSMOS:
//       return {
//         ...state,
//         config: {
//           ...state.config,
//           alerts: {
//             ...state.config.alerts,
//             thresholds: {
//               ...state.config.alerts.thresholds,
//               [action.payload.alertID]: {
//                 ...state.config.alerts.thresholds[action.payload.alertID],
//                 critical: {
//                   ...state.config.alerts.thresholds[action.payload.alertID].critical,
//                   delay: action.payload.delay,
//                 },
//               },
//             },
//           },
//         },
//       };
//     case UPDATE_CRITICAL_REPEAT_COSMOS:
//       return {
//         ...state,
//         config: {
//           ...state.config,
//           alerts: {
//             ...state.config.alerts,
//             thresholds: {
//               ...state.config.alerts.thresholds,
//               [action.payload.alertID]: {
//                 ...state.config.alerts.thresholds[action.payload.alertID],
//                 critical: {
//                   ...state.config.alerts.thresholds[action.payload.alertID].critical,
//                   repeat: action.payload.repeat,
//                 },
//               },
//             },
//           },
//         },
//       };
//     case UPDATE_CRITICAL_THRESHOLD_COSMOS:
//       return {
//         ...state,
//         config: {
//           ...state.config,
//           alerts: {
//             ...state.config.alerts,
//             thresholds: {
//               ...state.config.alerts.thresholds,
//               [action.payload.alertID]: {
//                 ...state.config.alerts.thresholds[action.payload.alertID],
//                 critical: {
//                   ...state.config.alerts.thresholds[action.payload.alertID].critical,
//                   threshold: action.payload.threshold,
//                 },
//               },
//             },
//           },
//         },
//       };
//     case UPDATE_CRITICAL_TIMEWINDOW_COSMOS:
//       return {
//         ...state,
//         config: {
//           ...state.config,
//           alerts: {
//             ...state.config.alerts,
//             thresholds: {
//               ...state.config.alerts.thresholds,
//               [action.payload.alertID]: {
//                 ...state.config.alerts.thresholds[action.payload.alertID],
//                 critical: {
//                   ...state.config.alerts.thresholds[action.payload.alertID].critical,
//                   timewindow: action.payload.timewindow,
//                 },
//               },
//             },
//           },
//         },
//       };
//     case UPDATE_CRITICAL_ENABLED_COSMOS:
//       return {
//         ...state,
//         config: {
//           ...state.config,
//           alerts: {
//             ...state.config.alerts,
//             thresholds: {
//               ...state.config.alerts.thresholds,
//               [action.payload.alertID]: {
//                 ...state.config.alerts.thresholds[action.payload.alertID],
//                 critical: {
//                   ...state.config.alerts.thresholds[action.payload.alertID].critical,
//                   enabled: action.payload.enabled,
//                 },
//               },
//             },
//           },
//         },
//       };
//     case UPDATE_ALERT_ENABLED_COSMOS:
//       return {
//         ...state,
//         config: {
//           ...state.config,
//           alerts: {
//             ...state.config.alerts,
//             thresholds: {
//               ...state.config.alerts.thresholds,
//               [action.payload.alertID]: {
//                 ...state.config.alerts.thresholds[action.payload.alertID],
//                 enabled: action.payload.enabled,
//               },
//             },
//           },
//         },
//       };
//     case UPDATE_ALERT_SEVERTY_LEVEL_COSMOS:
//       return {
//         ...state,
//         config: {
//           ...state.config,
//           alerts: {
//             ...state.config.alerts,
//             severties: {
//               ...state.config.alerts.severties,
//               [action.payload.alertID]: {
//                 ...state.config.alerts.severties[action.payload.alertID],
//                 severity: action.payload.severity,
//               },
//             },
//           },
//         },
//       };
//     case UPDATE_ALERT_SEVERTY_ENABLED_COSMOS:
//       return {
//         ...state,
//         config: {
//           ...state.config,
//           alerts: {
//             ...state.config.alerts,
//             severties: {
//               ...state.config.alerts.severties,
//               [action.payload.alertID]: {
//                 ...state.config.alerts.severties[action.payload.alertID],
//                 enabled: action.payload.enabled,
//               },
//             },
//           },
//         },
//       };
//     default:
//       return state;
//   }
// }

// export default cosmosChainsReducer;
