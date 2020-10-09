import _ from 'lodash';
import { combineReducers } from 'redux';
import { INFO, WARNING, CRITICAL } from '../../constants/constants';
import {
  ADD_CHAIN_SUBSTRATE, ADD_NODE_SUBSTRATE, REMOVE_NODE_SUBSTRATE,
  REMOVE_CHAIN_SUBSTRATE, UPDATE_CHAIN_NAME, RESET_CHAIN_SUBSTRATE, ADD_REPOSITORY,
  REMOVE_REPOSITORY, ADD_TELEGRAM_CHANNEL,
  REMOVE_TELEGRAM_CHANNEL, ADD_TWILIO_CHANNEL, REMOVE_TWILIO_CHANNEL,
  ADD_EMAIL_CHANNEL, REMOVE_EMAIL_CHANNEL, ADD_OPSGENIE_CHANNEL,
  REMOVE_OPSGENIE_CHANNEL, ADD_PAGERDUTY_CHANNEL, REMOVE_PAGERDUTY_CHANNEL,
  UPDATE_REPEAT_ALERT, UPDATE_TIMEWINDOW_ALERT, UPDATE_THRESHOLD_ALERT,
  UPDATE_SEVERITY_ALERT, LOAD_CONFIG_SUBSTRATE,
} from '../actions/types';

const substrateRepeatAlerts = {
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

const substrateTimeWindowAlerts = {
  byId: {
    1: {
      name: 'No change in best block height above warning threshold',
      warning: {
        threshold: 30,
        timewindow: 360,
        enabled: true,
      },
      critical: {
        threshold: 60,
        timewindow: 3600,
        enabled: true,
      },
      enabled: true,
    },
    2: {
      name: 'No change in finalized block height above warning threshold',
      warning: {
        threshold: 30,
        timewindow: 360,
        enabled: true,
      },
      critical: {
        threshold: 60,
        timewindow: 3600,
        enabled: true,
      },
      enabled: true,
    },
  },
  allIds: ['1', '2'],
};

const substrateThresholdAlerts = {
  byId: {
    1: {
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
    2: {
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
    3: {
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
    4: {
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
    5: {
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
    6: {
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
    7: {
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
  },
  allIds: ['1', '2', '3', '4', '5', '6', '7'],
};

const substrateSeverityAlerts = {
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
      name: 'Validator was declared as offline by the blockchain',
      severity: WARNING,
      enabled: true,
    },
    9: {
      name: 'Validator did not author a block and sent no heartbeats in the previous session',
      severity: WARNING,
      enabled: false,
    },
    10: {
      name: 'A new payout is pending',
      severity: WARNING,
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
    15: {
      name: 'Bonded balance increased',
      severity: INFO,
      enabled: false,
    },
    16: {
      name: 'Bonded balance decreased',
      severity: INFO,
      enabled: false,
    },
    17: {
      name: 'Free balance increased',
      severity: INFO,
      enabled: false,
    },
    18: {
      name: 'Free balance decreased',
      severity: INFO,
      enabled: false,
    },
    19: {
      name: 'Reserved balance increased',
      severity: INFO,
      enabled: false,
    },
    20: {
      name: 'Reserved balance decreased',
      severity: INFO,
      enabled: false,
    },
    21: {
      name: 'Nominated balance increased',
      severity: INFO,
      enabled: false,
    },
    22: {
      name: 'Nominated balance decreased',
      severity: INFO,
      enabled: false,
    },
    23: {
      name: 'Validator is not elected for next session',
      severity: WARNING,
      enabled: true,
    },
    24: {
      name: 'Validator has been disabled in session',
      severity: CRITICAL,
      enabled: true,
    },
    25: {
      name: 'New Council proposal',
      severity: INFO,
      enabled: true,
    },
    26: {
      name: 'Validator is now part of the council',
      severity: INFO,
      enabled: true,
    },
    27: {
      name: 'Validator is no longer part of the council',
      severity: INFO,
      enabled: true,
    },
    28: {
      name: 'A new treasury proposal has been submitted',
      severity: INFO,
      enabled: true,
    },
    29: {
      name: 'A new tip proposal has been submitted',
      severity: INFO,
      enabled: true,
    },
    30: {
      name: 'New Referendum submitted',
      severity: INFO,
      enabled: true,
    },
    31: {
      name: 'Referendum completed',
      severity: INFO,
      enabled: true,
    },
  },
  allIds: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13',
    '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26',
    '27', '28', '29', '30', '31'],
};

// Reducers to add and remove substrate node configurations from global state
function nodesById(state = {}, action) {
  switch (action.type) {
    case ADD_NODE_SUBSTRATE:
      return {
        ...state,
        [action.payload.id]: action.payload,
      };
    case REMOVE_NODE_SUBSTRATE:
      return _.omit(state, action.payload.id);
    default:
      return state;
  }
}

// Reducers to add and remove from list of all substrate nodes
function allNodes(state = [], action) {
  switch (action.type) {
    case ADD_NODE_SUBSTRATE:
      return state.concat(action.payload.id);
    case REMOVE_NODE_SUBSTRATE:
      return state.filter((config) => config !== action.payload.id);
    default:
      return state;
  }
}

const SubstrateNodesReducer = combineReducers({
  byId: nodesById,
  allIds: allNodes,
});

function substrateChainsById(state = {}, action) {
  switch (action.type) {
    case ADD_CHAIN_SUBSTRATE:
      return {
        ...state,
        [action.payload.id]: {
          id: action.payload.id,
          chainName: action.payload.chainName,
          nodes: [],
          repositories: [],
          alerts: [],
          telegrams: [],
          twilios: [],
          emails: [],
          pagerduties: [],
          opsgenies: [],
          repeatAlerts: substrateRepeatAlerts,
          timeWindowAlerts: substrateTimeWindowAlerts,
          thresholdAlerts: substrateThresholdAlerts,
          severityAlerts: substrateSeverityAlerts,
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
    case REMOVE_CHAIN_SUBSTRATE:
      return _.omit(state, action.payload.id);
    case ADD_NODE_SUBSTRATE:
      return {
        ...state,
        [action.payload.parentId]: {
          ...state[action.payload.parentId],
          nodes: state[action.payload.parentId].nodes.concat(action.payload.id),
        },
      };
    case REMOVE_NODE_SUBSTRATE:
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

function allSubstrateChains(state = [], action) {
  switch (action.type) {
    case ADD_CHAIN_SUBSTRATE:
      return state.concat(action.payload.id);
    case REMOVE_CHAIN_SUBSTRATE:
      return state.filter((config) => config !== action.payload.id);
    default:
      return state;
  }
}

const SubstrateChainsReducer = combineReducers({
  byId: substrateChainsById,
  allIds: allSubstrateChains,
});

function CurrentSubstrateChain(state = '', action) {
  switch (action.type) {
    case ADD_CHAIN_SUBSTRATE:
      return action.payload.id;
    case RESET_CHAIN_SUBSTRATE:
      return '';
    case LOAD_CONFIG_SUBSTRATE:
      return action.payload.id;
    default:
      return state;
  }
}

export {
  SubstrateNodesReducer, SubstrateChainsReducer, CurrentSubstrateChain,
};
