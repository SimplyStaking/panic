import _ from 'lodash';
import { combineReducers } from 'redux';
import {
  ADD_CHAIN_COSMOS, ADD_NODE_COSMOS, ADD_REPOSITORY_COSMOS, REMOVE_NODE_COSMOS,
  REMOVE_REPOSITORY_COSMOS, ADD_KMS_COSMOS, REMOVE_KMS_COSMOS, SET_ALERTS_COSMOS,
  ADD_CONFIG_COSMOS, REMOVE_CONFIG_COSMOS, RESET_CONFIG_COSMOS,
  LOAD_CONFIG_COSMOS, ADD_TELEGRAM_CHANNEL_COSMOS,
  REMOVE_TELEGRAM_CHANNEL_COSMOS, ADD_TWILIO_CHANNEL_COSMOS,
  REMOVE_TWILIO_CHANNEL_COSMOS, ADD_EMAIL_CHANNEL_COSMOS,
  REMOVE_EMAIL_CHANNEL_COSMOS, ADD_PAGERDUTY_CHANNEL_COSMOS,
  REMOVE_PAGERDUTY_CHANNEL_COSMOS, ADD_OPSGENIE_CHANNEL_COSMOS,
  REMOVE_OPSGENIE_CHANNEL_COSMOS, UPDATE_WARNING_DELAY_COSMOS,
  UPDATE_WARNING_REPEAT_COSMOS, UPDATE_WARNING_THRESHOLD_COSMOS,
  UPDATE_WARNING_TIMEWINDOW_COSMOS, UPDATE_WARNING_ENABLED_COSMOS,
  UPDATE_CRITICAL_DELAY_COSMOS, UPDATE_CRITICAL_REPEAT_COSMOS,
  UPDATE_CRITICAL_THRESHOLD_COSMOS, UPDATE_CRITICAL_TIMEWINDOW_COSMOS,
  UPDATE_CRITICAL_ENABLED_COSMOS, UPDATE_ALERT_ENABLED_COSMOS,
  UPDATE_ALERT_SEVERTY_LEVEL_COSMOS, UPDATE_ALERT_SEVERTY_ENABLED_COSMOS,
} from '../actions/types';

import { INFO, WARNING, CRITICAL } from '../../constants/constants';

// const initialstate = {
//   cosmosConfigs: [],
//   config: {
//     chainName: '',
//     nodes: [],
//     repositories: [],
//     kmses: [],
//     channels: [],
//     telegrams: [],
//     emails: [],
//     opsgenies: [],
//     pagerduties: [],
//     twilios: [],
//     alerts: {
//       thresholds: {
//         alert1: {
//           name: 'Cannot access validator',
//           warning: {
//             delay: 60,
//             repeat: 0,
//             enabled: true,
//           },
//           critical: {
//             delay: 60,
//             repeat: 300,
//             enabled: true,
//           },
//           enabled: true,
//         },
//         alert2: {
//           name: 'Cannot access node',
//           warning: {
//             delay: 60,
//             repeat: 300,
//             enabled: true,
//           },
//           critical: {
//             delay: 120,
//             repeat: 300,
//             enabled: false,
//           },
//           enabled: true,
//         },
//         alert3: {
//           name: 'Lost connection with specific peer',
//           warning: {
//             delay: 60,
//             enabled: true,
//           },
//           critical: {
//             delay: 120,
//             enabled: false,
//           },
//           enabled: true,
//         },
//         alert4: {
//           name: 'Peer count decreased',
//           warning: {
//             threshold: 3,
//             enabled: true,
//           },
//           critical: {
//             threshold: 2,
//             enabled: true,
//           },
//           enabled: true,
//         },
//         alert5: {
//           name: 'Missed Blocks',
//           warning: {
//             threshold: 20,
//             timewindow: 360,
//             enabled: true,
//           },
//           critical: {
//             threshold: 100,
//             timewindow: 3600,
//             enabled: true,
//           },
//           enabled: true,
//         },
//         alert6: {
//           name: 'No change in block height',
//           warning: {
//             threshold: 180,
//             enabled: true,
//           },
//           critical: {
//             threshold: 300,
//             enabled: true,
//           },
//           enabled: true,
//         },
//         alert7: {
//           name: 'Time of last pre-commit/pre-vote activity is above threshold',
//           warning: {
//             threshold: 60,
//             enabled: true,
//           },
//           critical: {
//             threshold: 180,
//             enabled: true,
//           },
//           enabled: true,
//         },
//         alert8: {
//           name: 'Mempool Size',
//           warning: {
//             threshold: 85,
//             enabled: true,
//           },
//           critical: {
//             threshold: 95,
//             enabled: true,
//           },
//           enabled: true,
//         },
//         alert9: {
//           name: 'System CPU usage increased',
//           warning: {
//             threshold: 85,
//             enabled: true,
//           },
//           critical: {
//             threshold: 95,
//             enabled: true,
//           },
//           enabled: true,
//         },
//         alert10: {
//           name: 'System storage usage increased',
//           warning: {
//             threshold: 85,
//             enabled: true,
//           },
//           critical: {
//             threshold: 95,
//             enabled: true,
//           },
//           enabled: true,
//         },
//         alert11: {
//           name: 'System RAM usage increased',
//           warning: {
//             threshold: 85,
//             enabled: true,
//           },
//           critical: {
//             threshold: 95,
//             enabled: true,
//           },
//           enabled: true,
//         },
//         alert12: {
//           name: 'System network usage increased',
//           warning: {
//             threshold: 85,
//             enabled: true,
//           },
//           critical: {
//             threshold: 95,
//             enabled: true,
//           },
//           enabled: true,
//         },
//         alert13: {
//           name: 'Open File Descriptors increased',
//           warning: {
//             threshold: 85,
//             enabled: true,
//           },
//           critical: {
//             threshold: 95,
//             enabled: true,
//           },
//           enabled: true,
//         },
//       },
//       severties: {
//         alert1: {
//           name: 'Validator inaccessible on startup',
//           severity: CRITICAL,
//           enabled: true,
//         },
//         alert2: {
//           name: 'Node inaccessible on startup',
//           severity: WARNING,
//           enabled: true,
//         },
//         alert3: {
//           name: 'Slashed',
//           severity: CRITICAL,
//           enabled: true,
//         },
//         alert4: {
//           name: 'Node is syncing',
//           severity: WARNING,
//           enabled: true,
//         },
//         alert5: {
//           name: 'Validator is not active in this session',
//           severity: WARNING,
//           enabled: true,
//         },
//         alert6: {
//           name: 'Validator set size increased',
//           severity: INFO,
//           enabled: true,
//         },
//         alert7: {
//           name: 'Validator set size decreased',
//           severity: INFO,
//           enabled: true,
//         },
//         alert8: {
//           name: 'Validator is jailed',
//           severity: CRITICAL,
//           enabled: true,
//         },
//         alert9: {
//           name: 'Voting power increased',
//           severity: INFO,
//           enabled: false,
//         },
//         alert10: {
//           name: 'Validator power decreased',
//           severity: INFO,
//           enabled: false,
//         },
//         alert11: {
//           name: 'New proposal submitted',
//           severity: INFO,
//           enabled: false,
//         },
//         alert12: {
//           name: 'Proposal conducted',
//           severity: INFO,
//           enabled: false,
//         },
//         alert13: {
//           name: 'Delegated balance increase',
//           severity: INFO,
//           enabled: false,
//         },
//         alert14: {
//           name: 'Delegated balance decrease',
//           severity: INFO,
//           enabled: false,
//         },
//       },
//     },
//   },
// };

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

export {
  CosmosNodesReducer,
};

function cosmosChainsReducer(state = {}, action) {
  switch (action.type) {
    case ADD_CHAIN_COSMOS:
      return {
        ...state,
        config: {
          ...state.config,
          chainName: action.payload.chainName,
        },
      };
    case ADD_REPOSITORY_COSMOS:
      return {
        ...state,
        config: {
          ...state.config,
          repositories: state.config.repositories.concat(action.payload),
        },
      };
    case REMOVE_REPOSITORY_COSMOS:
      return {
        ...state,
        config: {
          ...state.config,
          repositories: state.config.repositories.filter(
            (repository) => repository !== action.payload,
          ),
        },
      };
    case ADD_KMS_COSMOS:
      return {
        ...state,
        config: {
          ...state.config,
          kmses: state.config.kmses.concat(action.payload),
        },
      };
    case REMOVE_KMS_COSMOS:
      return {
        ...state,
        config: {
          ...state.config,
          kmses: state.config.kmses.filter(
            (kms) => kms !== action.payload,
          ),
        },
      };
    case ADD_TELEGRAM_CHANNEL_COSMOS:
      return {
        ...state,
        config: {
          ...state.config,
          telegrams: state.config.telegrams.concat(action.payload),
        },
      };
    case REMOVE_TELEGRAM_CHANNEL_COSMOS:
      return {
        ...state,
        config: {
          ...state.config,
          telegrams: state.config.telegrams.filter(
            (telegram) => telegram !== action.payload,
          ),
        },
      };
    case ADD_OPSGENIE_CHANNEL_COSMOS:
      return {
        ...state,
        config: {
          ...state.config,
          opsgenies: state.config.opsgenies.concat(action.payload),
        },
      };
    case REMOVE_OPSGENIE_CHANNEL_COSMOS:
      return {
        ...state,
        config: {
          ...state.config,
          opsgenies: state.config.opsgenies.filter(
            (opsgenie) => opsgenie !== action.payload,
          ),
        },
      };
    case ADD_EMAIL_CHANNEL_COSMOS:
      return {
        ...state,
        config: {
          ...state.config,
          emails: state.config.emails.concat(action.payload),
        },
      };
    case REMOVE_EMAIL_CHANNEL_COSMOS:
      return {
        ...state,
        config: {
          ...state.config,
          emails: state.config.emails.filter(
            (email) => email !== action.payload,
          ),
        },
      };
    case ADD_TWILIO_CHANNEL_COSMOS:
      return {
        ...state,
        config: {
          ...state.config,
          twilios: state.config.twilios.concat(action.payload),
        },
      };
    case REMOVE_TWILIO_CHANNEL_COSMOS:
      return {
        ...state,
        config: {
          ...state.config,
          twilios: state.config.twilios.filter(
            (twilio) => twilio !== action.payload,
          ),
        },
      };
    case ADD_PAGERDUTY_CHANNEL_COSMOS:
      return {
        ...state,
        config: {
          ...state.config,
          pagerduties: state.config.pagerduties.concat(action.payload),
        },
      };
    case REMOVE_PAGERDUTY_CHANNEL_COSMOS:
      return {
        ...state,
        config: {
          ...state.config,
          pagerduties: state.config.pagerduties.filter(
            (pagerduty) => pagerduty !== action.payload,
          ),
        },
      };
    case SET_ALERTS_COSMOS:
      return {
        ...state,
        config: {
          ...state.config,
          alerts: action.payload.alerts,
        },
      };
    case ADD_CONFIG_COSMOS:
      return {
        ...state,
        cosmosConfigs: state.cosmosConfigs.concat(state.config),
      };
    case REMOVE_CONFIG_COSMOS:
      return {
        ...state,
        cosmosConfigs: state.cosmosConfigs.filter(
          (cosmosConfig) => cosmosConfig !== action.payload,
        ),
      };
    case RESET_CONFIG_COSMOS:
      return {
        ...state,
        config: initialstate.config,
      };
    case LOAD_CONFIG_COSMOS:
      return {
        ...state,
        config: state.cosmosConfigs.filter(
          (cosmosConfig) => cosmosConfig === action.payload,
        )[0],
      };
    case UPDATE_WARNING_DELAY_COSMOS:
      return {
        ...state,
        config: {
          ...state.config,
          alerts: {
            ...state.config.alerts,
            thresholds: {
              ...state.config.alerts.thresholds,
              [action.payload.alertID]: {
                ...state.config.alerts.thresholds[action.payload.alertID],
                warning: {
                  ...state.config.alerts.thresholds[action.payload.alertID].warning,
                  delay: action.payload.delay,
                },
              },
            },
          },
        },
      };
    case UPDATE_WARNING_REPEAT_COSMOS:
      return {
        ...state,
        config: {
          ...state.config,
          alerts: {
            ...state.config.alerts,
            thresholds: {
              ...state.config.alerts.thresholds,
              [action.payload.alertID]: {
                ...state.config.alerts.thresholds[action.payload.alertID],
                warning: {
                  ...state.config.alerts.thresholds[action.payload.alertID].warning,
                  repeat: action.payload.repeat,
                },
              },
            },
          },
        },
      };
    case UPDATE_WARNING_THRESHOLD_COSMOS:
      return {
        ...state,
        config: {
          ...state.config,
          alerts: {
            ...state.config.alerts,
            thresholds: {
              ...state.config.alerts.thresholds,
              [action.payload.alertID]: {
                ...state.config.alerts.thresholds[action.payload.alertID],
                warning: {
                  ...state.config.alerts.thresholds[action.payload.alertID].warning,
                  threshold: action.payload.threshold,
                },
              },
            },
          },
        },
      };
    case UPDATE_WARNING_TIMEWINDOW_COSMOS:
      return {
        ...state,
        config: {
          ...state.config,
          alerts: {
            ...state.config.alerts,
            thresholds: {
              ...state.config.alerts.thresholds,
              [action.payload.alertID]: {
                ...state.config.alerts.thresholds[action.payload.alertID],
                warning: {
                  ...state.config.alerts.thresholds[action.payload.alertID].warning,
                  timewindow: action.payload.timewindow,
                },
              },
            },
          },
        },
      };
    case UPDATE_WARNING_ENABLED_COSMOS:
      return {
        ...state,
        config: {
          ...state.config,
          alerts: {
            ...state.config.alerts,
            thresholds: {
              ...state.config.alerts.thresholds,
              [action.payload.alertID]: {
                ...state.config.alerts.thresholds[action.payload.alertID],
                warning: {
                  ...state.config.alerts.thresholds[action.payload.alertID].warning,
                  enabled: action.payload.enabled,
                },
              },
            },
          },
        },
      };
    case UPDATE_CRITICAL_DELAY_COSMOS:
      return {
        ...state,
        config: {
          ...state.config,
          alerts: {
            ...state.config.alerts,
            thresholds: {
              ...state.config.alerts.thresholds,
              [action.payload.alertID]: {
                ...state.config.alerts.thresholds[action.payload.alertID],
                critical: {
                  ...state.config.alerts.thresholds[action.payload.alertID].critical,
                  delay: action.payload.delay,
                },
              },
            },
          },
        },
      };
    case UPDATE_CRITICAL_REPEAT_COSMOS:
      return {
        ...state,
        config: {
          ...state.config,
          alerts: {
            ...state.config.alerts,
            thresholds: {
              ...state.config.alerts.thresholds,
              [action.payload.alertID]: {
                ...state.config.alerts.thresholds[action.payload.alertID],
                critical: {
                  ...state.config.alerts.thresholds[action.payload.alertID].critical,
                  repeat: action.payload.repeat,
                },
              },
            },
          },
        },
      };
    case UPDATE_CRITICAL_THRESHOLD_COSMOS:
      return {
        ...state,
        config: {
          ...state.config,
          alerts: {
            ...state.config.alerts,
            thresholds: {
              ...state.config.alerts.thresholds,
              [action.payload.alertID]: {
                ...state.config.alerts.thresholds[action.payload.alertID],
                critical: {
                  ...state.config.alerts.thresholds[action.payload.alertID].critical,
                  threshold: action.payload.threshold,
                },
              },
            },
          },
        },
      };
    case UPDATE_CRITICAL_TIMEWINDOW_COSMOS:
      return {
        ...state,
        config: {
          ...state.config,
          alerts: {
            ...state.config.alerts,
            thresholds: {
              ...state.config.alerts.thresholds,
              [action.payload.alertID]: {
                ...state.config.alerts.thresholds[action.payload.alertID],
                critical: {
                  ...state.config.alerts.thresholds[action.payload.alertID].critical,
                  timewindow: action.payload.timewindow,
                },
              },
            },
          },
        },
      };
    case UPDATE_CRITICAL_ENABLED_COSMOS:
      return {
        ...state,
        config: {
          ...state.config,
          alerts: {
            ...state.config.alerts,
            thresholds: {
              ...state.config.alerts.thresholds,
              [action.payload.alertID]: {
                ...state.config.alerts.thresholds[action.payload.alertID],
                critical: {
                  ...state.config.alerts.thresholds[action.payload.alertID].critical,
                  enabled: action.payload.enabled,
                },
              },
            },
          },
        },
      };
    case UPDATE_ALERT_ENABLED_COSMOS:
      return {
        ...state,
        config: {
          ...state.config,
          alerts: {
            ...state.config.alerts,
            thresholds: {
              ...state.config.alerts.thresholds,
              [action.payload.alertID]: {
                ...state.config.alerts.thresholds[action.payload.alertID],
                enabled: action.payload.enabled,
              },
            },
          },
        },
      };
    case UPDATE_ALERT_SEVERTY_LEVEL_COSMOS:
      return {
        ...state,
        config: {
          ...state.config,
          alerts: {
            ...state.config.alerts,
            severties: {
              ...state.config.alerts.severties,
              [action.payload.alertID]: {
                ...state.config.alerts.severties[action.payload.alertID],
                severity: action.payload.severity,
              },
            },
          },
        },
      };
    case UPDATE_ALERT_SEVERTY_ENABLED_COSMOS:
      return {
        ...state,
        config: {
          ...state.config,
          alerts: {
            ...state.config.alerts,
            severties: {
              ...state.config.alerts.severties,
              [action.payload.alertID]: {
                ...state.config.alerts.severties[action.payload.alertID],
                enabled: action.payload.enabled,
              },
            },
          },
        },
      };
    default:
      return state;
  }
}

export default cosmosChainsReducer;
