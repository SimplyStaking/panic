/* eslint-disable no-prototype-builtins */
/* eslint-disable no-param-reassign */
import _ from 'lodash';
import { combineReducers } from 'redux';
import { INFO, WARNING, CRITICAL } from 'constants/constants';
import {
  ADD_CHAIN_SUBSTRATE,
  ADD_NODE_SUBSTRATE,
  REMOVE_NODE_SUBSTRATE,
  TOGGLE_NODE_MONITORING_SUBSTRATE,
  REMOVE_CHAIN_SUBSTRATE,
  UPDATE_CHAIN_NAME_SUBSTRATE,
  RESET_CHAIN_SUBSTRATE,
  ADD_REPOSITORY,
  REMOVE_REPOSITORY,
  ADD_DOCKER,
  REMOVE_DOCKER,
  UPDATE_REPEAT_ALERT,
  UPDATE_TIMEWINDOW_ALERT,
  UPDATE_THRESHOLD_ALERT,
  UPDATE_SEVERITY_ALERT,
  LOAD_CONFIG_SUBSTRATE,
  LOAD_REPEAT_ALERTS_SUBSTRATE,
  LOAD_TIMEWINDOW_ALERTS_SUBSTRATE,
  LOAD_THRESHOLD_ALERTS_SUBSTRATE,
  LOAD_SEVERITY_ALERTS_SUBSTRATE,
} from 'redux/actions/types';

const substrateRepeatAlerts = {
  byId: {},
  allIds: [],
};

const substrateTimeWindowAlerts = {
  byId: {},
  allIds: [],
};

const substrateThresholdAlerts = {
  byId: {
    1: {
      name: 'Cannot Access Validator',
      identifier: 'cannot_access_validator',
      description: 'Raised when a validator is unaccessible.',
      adornment: 'Seconds',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 0,
        enabled: true,
      },
      critical: {
        threshold: 120,
        repeat: 300,
        repeat_enabled: true,
        enabled: true,
      },
      enabled: true,
    },
    2: {
      name: 'Cannot Access Node',
      identifier: 'cannot_access_node',
      description: 'Raised when a node is unaccessible.',
      adornment: 'Seconds',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 0,
        enabled: true,
      },
      critical: {
        threshold: 300,
        repeat: 600,
        repeat_enabled: true,
        enabled: false,
      },
      enabled: true,
    },
    3: {
      name: 'No Change in Validator Best Block Height',
      identifier: 'no_change_in_best_block_height_validator',
      description: 'Raised when the best block height of a validator is unchanged.',
      adornment: 'Seconds',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 180,
        enabled: true,
      },
      critical: {
        threshold: 300,
        repeat: 180,
        repeat_enabled: true,
        enabled: true,
      },
      enabled: true,
    },
    4: {
      name: 'No Change in Node Best Block Height',
      identifier: 'no_change_in_best_block_height_node',
      description: 'Raised when the best block height of a node is unchanged.',
      adornment: 'Seconds',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 180,
        enabled: true,
      },
      critical: {
        threshold: 300,
        repeat: 300,
        repeat_enabled: true,
        enabled: false,
      },
      enabled: true,
    },
    5: {
      name: 'No Change in Validator Finalized Best Block Height',
      identifier: 'no_change_in_finalized_block_height_validator',
      description: 'Raised when the finalized best block height of a validator is unchanged.',
      adornment: 'Seconds',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 180,
        enabled: true,
      },
      critical: {
        threshold: 300,
        repeat: 180,
        repeat_enabled: true,
        enabled: true,
      },
      enabled: true,
    },
    6: {
      name: 'No Change in Node Finalized Best Block Height',
      identifier: 'no_change_in_finalized_block_height_node',
      description: 'Raised when the finalized best block height of a node is unchanged.',
      adornment: 'Seconds',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 180,
        enabled: true,
      },
      critical: {
        threshold: 300,
        repeat: 300,
        repeat_enabled: true,
        enabled: false,
      },
      enabled: true,
    },
    7: {
      name: 'Validator is Syncing',
      identifier: 'validator_is_syncing',
      description: 'This alert is raised when the validator\'s sync target height and best block height differ by a value greater than the threshold.',
      adornment: 'Blocks',
      adornment_time: 'Blocks',
      parent_id: '',
      warning: {
        threshold: 50,
        enabled: true,
      },
      critical: {
        threshold: 100,
        repeat: 300,
        repeat_enabled: true,
        enabled: true,
      },
      enabled: true,
    },
    8: {
      name: 'Node is Syncing',
      identifier: 'node_is_syncing',
      description: 'This alert is raised when the node\'s sync target height and best block height differ by a value greater than the threshold.',
      adornment: 'Blocks',
      adornment_time: 'Blocks',
      parent_id: '',
      warning: {
        threshold: 50,
        enabled: true,
      },
      critical: {
        threshold: 100,
        repeat: 300,
        repeat_enabled: true,
        enabled: false,
      },
      enabled: true,
    },
    9: {
      name: 'No Heartbeat and Did Not Author Block in Current Session Yet',
      identifier: 'no_heartbeat_did_not_author_block',
      description: 'Occurs when no heartbeat was recieved and no block has yet been '
          + 'authored in the current session.',
      adornment: 'Seconds',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 1800,
        enabled: true,
      },
      critical: {
        threshold: 2700,
        repeat: 300,
        repeat_enabled: false,
        enabled: true,
      },
      enabled: true,
    },
    10: {
      name: 'Payout Not Claimed',
      identifier: 'payout_not_claimed',
      description: 'Occurs when a payout has not been claimed yet after a number of eras.',
      adornment: 'Eras',
      adornment_time: 'Eras',
      parent_id: '',
      warning: {
        threshold: 30,
        enabled: true,
      },
      critical: {
        threshold: 60,
        repeat: 1,
        repeat_enabled: true,
        enabled: true,
      },
      enabled: true,
    },
    11: {
      name: 'System Is Down',
      identifier: 'system_is_down',
      description:
          'The Node Exporter URL is unreachable therefore the system is declared to be down.',
      adornment: 'Seconds',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 0,
        enabled: true,
      },
      critical: {
        threshold: 200,
        repeat: 300,
        repeat_enabled: true,
        enabled: true,
      },
      enabled: true,
    },
    12: {
      name: 'Open File Descriptors Increased',
      identifier: 'open_file_descriptors',
      description: 'Open File Descriptors alerted on based on percentage usage.',
      adornment: '%',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 85,
        enabled: true,
      },
      critical: {
        threshold: 95,
        repeat: 300,
        repeat_enabled: true,
        enabled: true,
      },
      enabled: true,
    },
    13: {
      name: 'System CPU usage increased',
      identifier: 'system_cpu_usage',
      description: 'System CPU alerted on based on percentage usage.',
      adornment: '%',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 85,
        enabled: true,
      },
      critical: {
        threshold: 95,
        repeat: 300,
        repeat_enabled: true,
        enabled: true,
      },
      enabled: true,
    },
    14: {
      name: 'System storage usage increased',
      identifier: 'system_storage_usage',
      description: 'System Storage alerted on based on percentage usage.',
      adornment: '%',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 85,
        enabled: true,
      },
      critical: {
        threshold: 95,
        repeat: 300,
        repeat_enabled: true,
        enabled: true,
      },
      enabled: true,
    },
    15: {
      name: 'System RAM usage increased',
      identifier: 'system_ram_usage',
      description: 'System RAM alerted on based on percentage usage.',
      adornment: '%',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 85,
        enabled: true,
      },
      critical: {
        threshold: 95,
        repeat: 300,
        repeat_enabled: true,
        enabled: true,
      },
      enabled: true,
    },
  },
  allIds: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15'],
};

const substrateSeverityAlerts = {
  byId: {
    16: {
      name: 'Not Active in Session',
      identifier: 'not_active_in_session',
      description: 'Occurs when a validator does not participate in a session.',
      severity: WARNING,
      parent_id: '',
      enabled: true,
    },
    17: {
      name: 'Is Disabled',
      identifier: 'is_disabled',
      description: 'Occurs when a validator is disabled.',
      severity: CRITICAL,
      parent_id: '',
      enabled: true,
    },
    18: {
      name: 'Not elected',
      identifier: 'not_elected',
      description: 'Occurs when a validator was not elected for next session.',
      severity: WARNING,
      parent_id: '',
      enabled: true,
    },
    19: {
      name: 'Bonded Amount Changed',
      identifier: 'bonded_amount_change',
      description: 'Occurs when the bonded amount of a validator is changed.',
      severity: INFO,
      parent_id: '',
      enabled: true,
    },
    20: {
      name: 'Offline',
      identifier: 'offline',
      description: 'Occurs when an offline event is generated for a validator.',
      severity: CRITICAL,
      parent_id: '',
      enabled: true,
    },
    21: {
      name: 'Slashed',
      identifier: 'slashed',
      description: 'Occurs when a validator has been slashed.',
      severity: CRITICAL,
      parent_id: '',
      enabled: true,
    },
    22: {
      name: 'Controller Address Change',
      identifier: 'controller_address_change',
      description: 'Occurs when the controller address changes.',
      severity: WARNING,
      parent_id: '',
      enabled: true,
    },
    23: {
      name: 'Grandpa is Stalled',
      identifier: 'grandpa_is_stalled',
      description: 'Occurs when the grandpa algorithm stalls.',
      severity: WARNING,
      parent_id: '',
      enabled: true,
    },
    24: {
      name: 'New proposal submitted',
      identifier: 'new_proposal',
      description: 'A new proposal has been submitted.',
      severity: INFO,
      parent_id: '',
      enabled: true,
    },
    25: {
      name: 'New Referendum',
      identifier: 'new_referendum',
      description: 'A new referendum has been submitted.',
      severity: INFO,
      parent_id: '',
      enabled: true,
    },
    26: {
      name: 'Referendum concluded',
      identifier: 'referendum_concluded',
      description: 'A referendum has been concluded.',
      severity: INFO,
      parent_id: '',
      enabled: true,
    },
  },
  allIds: ['16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26'],
};

// Reducers to add and remove substrate node configurations from global state
function nodesById(state = {}, action) {
  switch (action.type) {
    case ADD_NODE_SUBSTRATE:
      Object.keys(state).forEach((node) => {
        if (state[node].parent_id === action.payload.parent_id) {
          action.payload.monitor_network = state[node].monitor_network;
        }
      });
      return {
        ...state,
        [action.payload.id]: action.payload,
      };
    case REMOVE_NODE_SUBSTRATE:
      return _.omit(state, action.payload.id);
    case TOGGLE_NODE_MONITORING_SUBSTRATE:
      Object.keys(state).forEach((node) => {
        if (state[node].parent_id === action.payload.parent_id) {
          state[node].monitor_network = action.payload.monitor_network;
        }
      });
      return state;
    default:
      return state;
  }
}

// Reducers to add and remove from list of all substrate nodes
function allNodes(state = [], action) {
  switch (action.type) {
    case ADD_NODE_SUBSTRATE:
      if (state.includes(action.payload.id)) {
        return state;
      }
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
      if (state[action.payload.id] !== undefined) {
        return state;
      }
      return {
        ...state,
        [action.payload.id]: {
          id: action.payload.id,
          chain_name: action.payload.chain_name,
          nodes: [],
          githubRepositories: [],
          dockerHubs: [],
          repeatAlerts: substrateRepeatAlerts,
          timeWindowAlerts: substrateTimeWindowAlerts,
          thresholdAlerts: substrateThresholdAlerts,
          severityAlerts: substrateSeverityAlerts,
        },
      };
    case UPDATE_CHAIN_NAME_SUBSTRATE:
      return {
        ...state,
        [action.payload.id]: {
          ...state[action.payload.id],
          chain_name: action.payload.chain_name,
        },
      };
    case REMOVE_CHAIN_SUBSTRATE:
      return _.omit(state, action.payload.id);
    case ADD_NODE_SUBSTRATE:
      if (state[action.payload.parent_id].nodes.includes(action.payload.id)) {
        return state;
      }
      return {
        ...state,
        [action.payload.parent_id]: {
          ...state[action.payload.parent_id],
          nodes: state[action.payload.parent_id].nodes.concat(action.payload.id),
        },
      };
    case REMOVE_NODE_SUBSTRATE:
      return {
        ...state,
        [action.payload.parent_id]: {
          ...state[action.payload.parent_id],
          nodes: state[action.payload.parent_id].nodes.filter(
            (config) => config !== action.payload.id,
          ),
        },
      };
    case ADD_REPOSITORY:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (state[action.payload.parent_id] === undefined) {
        return state;
      }
      if (state[action.payload.parent_id].githubRepositories.includes(action.payload.id)) {
        return state;
      }
      return {
        ...state,
        [action.payload.parent_id]: {
          ...state[action.payload.parent_id],
          githubRepositories: state[action.payload.parent_id].githubRepositories.concat(
            action.payload.id,
          ),
        },
      };
    case REMOVE_REPOSITORY:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (state[action.payload.parent_id] === undefined) {
        return state;
      }
      return {
        ...state,
        [action.payload.parent_id]: {
          ...state[action.payload.parent_id],
          githubRepositories: state[action.payload.parent_id].githubRepositories.filter(
            (config) => config !== action.payload.id,
          ),
        },
      };
    case ADD_DOCKER:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (state[action.payload.parent_id] === undefined) {
        return state;
      }
      if (state[action.payload.parent_id].dockerHubs.includes(action.payload.id)) {
        return state;
      }
      return {
        ...state,
        [action.payload.parent_id]: {
          ...state[action.payload.parent_id],
          dockerHubs: state[action.payload.parent_id].dockerHubs.concat(action.payload.id),
        },
      };
    case REMOVE_DOCKER:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (state[action.payload.parent_id] === undefined) {
        return state;
      }
      return {
        ...state,
        [action.payload.parent_id]: {
          ...state[action.payload.parent_id],
          dockerHubs: state[action.payload.parent_id].dockerHubs.filter(
            (config) => config !== action.payload.id,
          ),
        },
      };
    case UPDATE_REPEAT_ALERT:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (state[action.payload.parent_id] === undefined) {
        return state;
      }
      return {
        ...state,
        [action.payload.parent_id]: {
          ...state[action.payload.parent_id],
          repeatAlerts: {
            ...state[action.payload.parent_id].repeatAlerts,
            byId: {
              ...state[action.payload.parent_id].repeatAlerts.byId,
              [action.payload.id]: action.payload.alert,
            },
          },
        },
      };
    case LOAD_REPEAT_ALERTS_SUBSTRATE:
      return {
        ...state,
        [action.payload.parent_id]: {
          ...state[action.payload.parent_id],
          repeatAlerts: action.payload.alerts,
        },
      };
    case UPDATE_TIMEWINDOW_ALERT:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (state[action.payload.parent_id] === undefined) {
        return state;
      }
      return {
        ...state,
        [action.payload.parent_id]: {
          ...state[action.payload.parent_id],
          timeWindowAlerts: {
            ...state[action.payload.parent_id].timeWindowAlerts,
            byId: {
              ...state[action.payload.parent_id].timeWindowAlerts.byId,
              [action.payload.id]: action.payload.alert,
            },
          },
        },
      };
    case LOAD_TIMEWINDOW_ALERTS_SUBSTRATE:
      return {
        ...state,
        [action.payload.parent_id]: {
          ...state[action.payload.parent_id],
          timeWindowAlerts: action.payload.alerts,
        },
      };
    case UPDATE_THRESHOLD_ALERT:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (state[action.payload.parent_id] === undefined) {
        return state;
      }
      return {
        ...state,
        [action.payload.parent_id]: {
          ...state[action.payload.parent_id],
          thresholdAlerts: {
            ...state[action.payload.parent_id].thresholdAlerts,
            byId: {
              ...state[action.payload.parent_id].thresholdAlerts.byId,
              [action.payload.id]: action.payload.alert,
            },
          },
        },
      };
    case LOAD_THRESHOLD_ALERTS_SUBSTRATE:
      return {
        ...state,
        [action.payload.parent_id]: {
          ...state[action.payload.parent_id],
          thresholdAlerts: action.payload.alerts,
        },
      };
    case UPDATE_SEVERITY_ALERT:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (state[action.payload.parent_id] === undefined) {
        return state;
      }
      return {
        ...state,
        [action.payload.parent_id]: {
          ...state[action.payload.parent_id],
          severityAlerts: {
            ...state[action.payload.parent_id].severityAlerts,
            byId: {
              ...state[action.payload.parent_id].severityAlerts.byId,
              [action.payload.id]: action.payload.alert,
            },
          },
        },
      };
    case LOAD_SEVERITY_ALERTS_SUBSTRATE:
      return {
        ...state,
        [action.payload.parent_id]: {
          ...state[action.payload.parent_id],
          severityAlerts: action.payload.alerts,
        },
      };
    default:
      return state;
  }
}

function allSubstrateChains(state = [], action) {
  switch (action.type) {
    case ADD_CHAIN_SUBSTRATE:
      if (state.includes(action.payload.id)) {
        return state;
      }
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
  SubstrateNodesReducer,
  SubstrateChainsReducer,
  CurrentSubstrateChain,
  substrateRepeatAlerts,
  substrateThresholdAlerts,
  substrateTimeWindowAlerts,
  substrateSeverityAlerts,
};
