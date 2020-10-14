import _ from 'lodash';
import { combineReducers } from 'redux';
import { INFO, WARNING, CRITICAL } from '../../constants/constants';
import {
  ADD_CHAIN_COSMOS, ADD_NODE_COSMOS, REMOVE_NODE_COSMOS,
  REMOVE_CHAIN_COSMOS, UPDATE_CHAIN_NAME, RESET_CHAIN_COSMOS, ADD_REPOSITORY,
  REMOVE_REPOSITORY, ADD_KMS, REMOVE_KMS, ADD_TELEGRAM_CHANNEL,
  REMOVE_TELEGRAM_CHANNEL, ADD_TWILIO_CHANNEL, REMOVE_TWILIO_CHANNEL,
  ADD_EMAIL_CHANNEL, REMOVE_EMAIL_CHANNEL, ADD_OPSGENIE_CHANNEL,
  REMOVE_OPSGENIE_CHANNEL, ADD_PAGERDUTY_CHANNEL, REMOVE_PAGERDUTY_CHANNEL,
  UPDATE_REPEAT_ALERT, UPDATE_TIMEWINDOW_ALERT, UPDATE_THRESHOLD_ALERT,
  UPDATE_SEVERITY_ALERT, LOAD_CONFIG_COSMOS,
} from '../actions/types';

const cosmosRepeatAlerts = {
  byId: {
    1: {
      name: 'Cannot access validator',
      warning: {
        delay: 60,
        repeat: 0,
        enabled: true,
      },
      critical: {
        delay: 60,
        repeat: 300,
        enabled: true,
      },
      enabled: true,
    },
    2: {
      name: 'Cannot access node',
      warning: {
        delay: 60,
        repeat: 300,
        enabled: true,
      },
      critical: {
        delay: 120,
        repeat: 300,
        enabled: false,
      },
      enabled: true,
    },
    3: {
      name: 'Lost connection with specific peer',
      warning: {
        delay: 60,
        repeat: 0,
        enabled: true,
      },
      critical: {
        delay: 120,
        repeat: 0,
        enabled: false,
      },
      enabled: true,
    },
  },
  allIds: ['1', '2', '3'],
};

const cosmosTimeWindowAlerts = {
  byId: {
    1: {
      name: 'Missed Blocks',
      warning: {
        threshold: 20,
        timewindow: 360,
        enabled: true,
      },
      critical: {
        threshold: 100,
        timewindow: 3600,
        enabled: true,
      },
      enabled: true,
    },
  },
  allIds: ['1'],
};

const cosmosThresholdAlerts = {
  byId: {
    1: {
      name: 'Open File Descriptors increased',
      warning: {
        threshold: 85,
        enabled: true,
      },
      critical: {
        threshold: 95,
        enabled: true,
      },
      enabled: true,
    },
    2: {
      name: 'Peer count decreased',
      warning: {
        threshold: 3,
        enabled: true,
      },
      critical: {
        threshold: 2,
        enabled: true,
      },
      enabled: true,
    },
    3: {
      name: 'No change in block height',
      warning: {
        threshold: 180,
        enabled: true,
      },
      critical: {
        threshold: 300,
        enabled: true,
      },
      enabled: true,
    },
    4: {
      name: 'Time of last pre-commit/pre-vote activity is above threshold',
      warning: {
        threshold: 60,
        enabled: true,
      },
      critical: {
        threshold: 180,
        enabled: true,
      },
      enabled: true,
    },
    5: {
      name: 'Mempool Size',
      warning: {
        threshold: 85,
        enabled: true,
      },
      critical: {
        threshold: 95,
        enabled: true,
      },
      enabled: true,
    },
    6: {
      name: 'System CPU usage increased',
      warning: {
        threshold: 85,
        enabled: true,
      },
      critical: {
        threshold: 95,
        enabled: true,
      },
      enabled: true,
    },
    7: {
      name: 'System storage usage increased',
      warning: {
        threshold: 85,
        enabled: true,
      },
      critical: {
        threshold: 95,
        enabled: true,
      },
      enabled: true,
    },
    8: {
      name: 'System RAM usage increased',
      warning: {
        threshold: 85,
        enabled: true,
      },
      critical: {
        threshold: 95,
        enabled: true,
      },
      enabled: true,
    },
    9: {
      name: 'System network usage increased',
      warning: {
        threshold: 85,
        enabled: true,
      },
      critical: {
        threshold: 95,
        enabled: true,
      },
      enabled: true,
    },
  },
  allIds: ['1', '2', '3', '4', '5', '6', '7', '8', '9'],
};

const cosmosSeverityAlerts = {
  byId: {
    1: {
      name: 'Validator inaccessible on startup',
      severity: CRITICAL,
      enabled: true,
    },
    2: {
      name: 'Node inaccessible on startup',
      severity: WARNING,
      enabled: true,
    },
    3: {
      name: 'Slashed',
      severity: CRITICAL,
      enabled: true,
    },
    4: {
      name: 'Node is syncing',
      severity: WARNING,
      enabled: true,
    },
    5: {
      name: 'Validator is not active in this session',
      severity: WARNING,
      enabled: true,
    },
    6: {
      name: 'Validator set size increased',
      severity: INFO,
      enabled: true,
    },
    7: {
      name: 'Validator set size decreased',
      severity: INFO,
      enabled: true,
    },
    8: {
      name: 'Validator is jailed',
      severity: CRITICAL,
      enabled: true,
    },
    9: {
      name: 'Voting power increased',
      severity: INFO,
      enabled: false,
    },
    10: {
      name: 'Validator power decreased',
      severity: INFO,
      enabled: false,
    },
    11: {
      name: 'New proposal submitted',
      severity: INFO,
      enabled: false,
    },
    12: {
      name: 'Proposal conducted',
      severity: INFO,
      enabled: false,
    },
    13: {
      name: 'Delegated balance increase',
      severity: INFO,
      enabled: false,
    },
    14: {
      name: 'Delegated balance decrease',
      severity: INFO,
      enabled: false,
    },
  },
  allIds: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
};

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
        [action.payload.id]: {
          id: action.payload.id,
          chainName: action.payload.chainName,
          nodes: [],
          kmses: [],
          repositories: [],
          alerts: [],
          telegrams: [],
          twilios: [],
          emails: [],
          pagerduties: [],
          opsgenies: [],
          repeatAlerts: cosmosRepeatAlerts,
          timeWindowAlerts: cosmosTimeWindowAlerts,
          thresholdAlerts: cosmosThresholdAlerts,
          severityAlerts: cosmosSeverityAlerts,
        },
      };
    case UPDATE_CHAIN_NAME:
      return {
        ...state,
        [action.payload.id]: {
          ...state[action.payload.id],
          chainName: action.payload.chainName,
        },
      };
    case REMOVE_CHAIN_COSMOS:
      return _.omit(state, action.payload.id);
    case ADD_NODE_COSMOS:
      return {
        ...state,
        [action.payload.parentId]: {
          ...state[action.payload.parentId],
          nodes: state[action.payload.parentId].nodes.concat(action.payload.id),
        },
      };
    case REMOVE_NODE_COSMOS:
      return {
        ...state,
        [action.payload.parentId]: {
          ...state[action.payload.parentId],
          nodes: state[action.payload.parentId].nodes.filter(
            (config) => config !== action.payload.id,
          ),
        },
      };
    case ADD_REPOSITORY:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (state[action.payload.parentId] === undefined) {
        return state;
      }
      return {
        ...state,
        [action.payload.parentId]: {
          ...state[action.payload.parentId],
          repositories: state[action.payload.parentId].repositories.concat(action.payload.id),
        },
      };
    case REMOVE_REPOSITORY:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (state[action.payload.parentId] === undefined) {
        return state;
      }
      return {
        ...state,
        [action.payload.parentId]: {
          ...state[action.payload.parentId],
          repositories: state[action.payload.parentId].repositories.filter(
            (config) => config !== action.payload.id,
          ),
        },
      };
    case ADD_KMS:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (state[action.payload.parentId] === undefined) {
        return state;
      }
      return {
        ...state,
        [action.payload.parentId]: {
          ...state[action.payload.parentId],
          kmses: state[action.payload.parentId].kmses.concat(action.payload.id),
        },
      };
    case REMOVE_KMS:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (state[action.payload.parentId] === undefined) {
        return state;
      }
      return {
        ...state,
        [action.payload.parentId]: {
          ...state[action.payload.parentId],
          kmses: state[action.payload.parentId].kmses.filter(
            (config) => config !== action.payload.id,
          ),
        },
      };
    case ADD_TELEGRAM_CHANNEL:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (state[action.payload.parentId] === undefined) {
        return state;
      }
      return {
        ...state,
        [action.payload.parentId]: {
          ...state[action.payload.parentId],
          telegrams: state[action.payload.parentId].telegrams.concat(action.payload.id),
        },
      };
    case REMOVE_TELEGRAM_CHANNEL:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (state[action.payload.parentId] === undefined) {
        return state;
      }
      return {
        ...state,
        [action.payload.parentId]: {
          ...state[action.payload.parentId],
          telegrams: state[action.payload.parentId].telegrams.filter(
            (config) => config !== action.payload.id,
          ),
        },
      };
    case ADD_TWILIO_CHANNEL:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (state[action.payload.parentId] === undefined) {
        return state;
      }
      return {
        ...state,
        [action.payload.parentId]: {
          ...state[action.payload.parentId],
          twilios: state[action.payload.parentId].twilios.concat(action.payload.id),
        },
      };
    case REMOVE_TWILIO_CHANNEL:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (state[action.payload.parentId] === undefined) {
        return state;
      }
      return {
        ...state,
        [action.payload.parentId]: {
          ...state[action.payload.parentId],
          twilios: state[action.payload.parentId].twilios.filter(
            (config) => config !== action.payload.id,
          ),
        },
      };
    case ADD_EMAIL_CHANNEL:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (state[action.payload.parentId] === undefined) {
        return state;
      }
      return {
        ...state,
        [action.payload.parentId]: {
          ...state[action.payload.parentId],
          emails: state[action.payload.parentId].emails.concat(action.payload.id),
        },
      };
    case REMOVE_EMAIL_CHANNEL:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (state[action.payload.parentId] === undefined) {
        return state;
      }
      return {
        ...state,
        [action.payload.parentId]: {
          ...state[action.payload.parentId],
          emails: state[action.payload.parentId].emails.filter(
            (config) => config !== action.payload.id,
          ),
        },
      };
    case ADD_PAGERDUTY_CHANNEL:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (state[action.payload.parentId] === undefined) {
        return state;
      }
      return {
        ...state,
        [action.payload.parentId]: {
          ...state[action.payload.parentId],
          pagerduties: state[action.payload.parentId].pagerduties.concat(action.payload.id),
        },
      };
    case REMOVE_PAGERDUTY_CHANNEL:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (state[action.payload.parentId] === undefined) {
        return state;
      }
      return {
        ...state,
        [action.payload.parentId]: {
          ...state[action.payload.parentId],
          pagerduties: state[action.payload.parentId].pagerduties.filter(
            (config) => config !== action.payload.id,
          ),
        },
      };
    case ADD_OPSGENIE_CHANNEL:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (state[action.payload.parentId] === undefined) {
        return state;
      }
      return {
        ...state,
        [action.payload.parentId]: {
          ...state[action.payload.parentId],
          opsgenies: state[action.payload.parentId].opsgenies.concat(action.payload.id),
        },
      };
    case REMOVE_OPSGENIE_CHANNEL:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (state[action.payload.parentId] === undefined) {
        return state;
      }
      return {
        ...state,
        [action.payload.parentId]: {
          ...state[action.payload.parentId],
          opsgenies: state[action.payload.parentId].opsgenies.filter(
            (config) => config !== action.payload.id,
          ),
        },
      };
    case UPDATE_REPEAT_ALERT:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (state[action.payload.parentId] === undefined) {
        return state;
      }
      return {
        ...state,
        [action.payload.parentId]: {
          ...state[action.payload.parentId],
          repeatAlerts: {
            ...state[action.payload.parentId].repeatAlerts,
            byId: {
              ...state[action.payload.parentId].repeatAlerts.byId,
              [action.payload.id]: action.payload.alert,
            },
          },
        },
      };
    case UPDATE_TIMEWINDOW_ALERT:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (state[action.payload.parentId] === undefined) {
        return state;
      }
      return {
        ...state,
        [action.payload.parentId]: {
          ...state[action.payload.parentId],
          timeWindowAlerts: {
            ...state[action.payload.parentId].timeWindowAlerts,
            byId: {
              ...state[action.payload.parentId].timeWindowAlerts.byId,
              [action.payload.id]: action.payload.alert,
            },
          },
        },
      };
    case UPDATE_THRESHOLD_ALERT:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (state[action.payload.parentId] === undefined) {
        return state;
      }
      return {
        ...state,
        [action.payload.parentId]: {
          ...state[action.payload.parentId],
          thresholdAlerts: {
            ...state[action.payload.parentId].thresholdAlerts,
            byId: {
              ...state[action.payload.parentId].thresholdAlerts.byId,
              [action.payload.id]: action.payload.alert,
            },
          },
        },
      };
    case UPDATE_SEVERITY_ALERT:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (state[action.payload.parentId] === undefined) {
        return state;
      }
      return {
        ...state,
        [action.payload.parentId]: {
          ...state[action.payload.parentId],
          severityAlerts: {
            ...state[action.payload.parentId].severityAlerts,
            byId: {
              ...state[action.payload.parentId].severityAlerts.byId,
              [action.payload.id]: action.payload.alert,
            },
          },
        },
      };
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
    case LOAD_CONFIG_COSMOS:
      return action.payload.id;
    default:
      return state;
  }
}

export {
  CosmosNodesReducer, CosmosChainsReducer, CurrentCosmosChain,
};
