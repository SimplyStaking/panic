/* eslint-disable no-prototype-builtins */
/* eslint-disable no-param-reassign */
import _ from 'lodash';
import { combineReducers } from 'redux';
import { INFO, WARNING, CRITICAL } from 'constants/constants';
import {
  ADD_CHAIN_COSMOS,
  ADD_NODE_COSMOS,
  REMOVE_NODE_COSMOS,
  TOGGLE_NODE_MONITORING_COSMOS,
  REMOVE_CHAIN_COSMOS,
  UPDATE_CHAIN_NAME_COSMOS,
  RESET_CHAIN_COSMOS,
  ADD_REPOSITORY,
  REMOVE_REPOSITORY,
  UPDATE_REPEAT_ALERT,
  UPDATE_TIMEWINDOW_ALERT,
  UPDATE_THRESHOLD_ALERT,
  UPDATE_SEVERITY_ALERT,
  LOAD_CONFIG_COSMOS,
  LOAD_REPEAT_ALERTS_COSMOS,
  LOAD_TIMEWINDOW_ALERTS_COSMOS,
  LOAD_THRESHOLD_ALERTS_COSMOS,
  LOAD_SEVERITY_ALERTS_COSMOS,
  ADD_DOCKER,
  REMOVE_DOCKER,
} from 'redux/actions/types';

const cosmosRepeatAlerts = {
  byId: {},
  allIds: [],
};

const cosmosThresholdAlerts = {
  byId: {
    1: {
      name: 'Cannot access validator',
      identifier: 'cannot_access_validator',
      description: 'If a validator is inaccessible you will be alerted.',
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
      name: 'Cannot access node',
      identifier: 'cannot_access_node',
      description: 'If a node is inaccessible you will be alerted.',
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
    4: {
      name: 'No change in block height for a validator.',
      identifier: 'no_change_in_block_height_validator',
      description: 'This alert is raised when there has not been a change in node block height over a period of time.',
      adornment: 'Seconds',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 30,
        enabled: true,
      },
      critical: {
        threshold: 60,
        repeat: 180,
        repeat_enabled: true,
        enabled: true,
      },
      enabled: true,
    },
    5: {
      name: 'No change in block height for a node.',
      identifier: 'no_change_in_block_height_node',
      description: 'This alert is raised when there has not been a change in node block height over a period of time.',
      adornment: 'Seconds',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 120,
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
    6: {
      name: 'Difference between monitored node heights.',
      identifier: 'block_height_difference',
      description: 'This alert is raised when the block height difference between multiple Cosmos nodes increases above thresholds.',
      adornment: 'Blocks',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 50,
        enabled: true,
      },
      critical: {
        threshold: 100,
        repeat: 300,
        repeat_enabled: false,
        enabled: false,
      },
      enabled: true,
    },
    7: {
      name: 'Open File Descriptors Increased',
      identifier: 'open_file_descriptors',
      description: 'Open File Descriptors alerted on based on percentage usage .',
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
    8: {
      name: 'System CPU Usage Increased',
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
    9: {
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
    10: {
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
    11: {
      name: 'Cannot access Prometheus for Validator.',
      identifier: 'cannot_access_prometheus_validator',
      description: 'The prometheus endpoint for a validator has not been accessible for some time.',
      adornment: '%',
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
    12: {
      name: 'Cannot access Prometheus for Node.',
      identifier: 'cannot_access_prometheus_node',
      description: 'The prometheus endpoint for a node has not been accessible for a some time.',
      adornment: '%',
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
    13: {
      name: 'Cannot access cosmos rest server for Validator.',
      identifier: 'cannot_access_cosmos_rest_validator',
      description: 'The Cosmos rest server for a validator has not been accessible for some time.',
      adornment: '%',
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
    14: {
      name: 'Cannot access cosmos rest server for Node.',
      identifier: 'cannot_access_cosmos_rest_node',
      description: 'The Cosmos rest server for a node has not been accessible for a some time.',
      adornment: '%',
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
    15: {
      name: 'Cannot access tendermint rpc for Validator.',
      identifier: 'cannot_access_tendermint_rpc_validator',
      description: 'The Tendermint RPC for a validator has not been accessible for some time.',
      adornment: '%',
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
    16: {
      name: 'Cannot access tendermint rpc for Node.',
      identifier: 'cannot_access_tendermint_rpc_node',
      description: 'The Tendermint RPC for a node has not been accessible for a some time.',
      adornment: '%',
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
  },
  allIds: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16'],
};

const cosmosTimeWindowAlerts = {
  byId: {
    17: {
      name: 'Missed block signatures within a time window.',
      identifier: 'missed_blocks',
      description: 'After a number of missed block signatures during a time window.',
      adornment_threshold: 'Blocks',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 10,
        time_window: 180,
        enabled: true,
      },
      critical: {
        threshold: 25,
        time_window: 300,
        repeat: 300,
        repeat_enabled: true,
        enabled: true,
      },
      enabled: true,
    },
  },
  allIds: ['17'],
};

const cosmosSeverityAlerts = {
  byId: {
    18: {
      name: 'Slashed',
      identifier: 'slashed',
      description: 'Occurs when your validator has been slashed.',
      severity: CRITICAL,
      parent_id: '',
      enabled: true,
    },
    19: {
      name: 'Node is syncing',
      identifier: 'node_is_syncing',
      description:
        'Occurs when your node is still catching up to the rest of '
        + 'the blockchain network in terms of block height.',
      severity: INFO,
      parent_id: '',
      enabled: true,
    },
    20: {
      name: 'Validator is syncing',
      identifier: 'validator_is_syncing',
      description:
        'Occurs when your validator is still catching up to the rest of '
        + 'the blockchain network in terms of block height.',
      severity: WARNING,
      parent_id: '',
      enabled: true,
    },
    21: {
      name: 'Validator not active in session',
      identifier: 'validator_not_active_in_session',
      description: 'If a validator is not active in the current session.',
      severity: CRITICAL,
      parent_id: '',
      enabled: true,
    },
    22: {
      name: 'Validator Is Jailed',
      identifier: 'validator_is_jailed',
      description: 'Status of validator jailed/not jailed.',
      severity: CRITICAL,
      parent_id: '',
      enabled: true,
    },
    23: {
      name: 'New proposal submitted',
      identifier: 'new_proposal',
      description: 'A new proposal has been submitted.',
      severity: INFO,
      parent_id: '',
      enabled: true,
    },
    24: {
      name: 'Proposal concluded',
      identifier: 'proposal_concluded',
      description: 'A proposal has been concluded.',
      severity: INFO,
      parent_id: '',
      enabled: true,
    },
  },
  allIds: ['18', '19', '20', '21', '22', '23', '24'],
};

// Reducers to add and remove cosmos node configurations from global state
function nodesById(state = {}, action) {
  switch (action.type) {
    case ADD_NODE_COSMOS:
      Object.keys(state).forEach((node) => {
        if (state[node].parent_id === action.payload.parent_id) {
          action.payload.monitor_network = state[node].monitor_network;
        }
      });
      return {
        ...state,
        [action.payload.id]: action.payload,
      };
    case REMOVE_NODE_COSMOS:
      return _.omit(state, action.payload.id);
    case TOGGLE_NODE_MONITORING_COSMOS:
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

// Reducers to add and remove from list of all cosmos nodes
function allNodes(state = [], action) {
  switch (action.type) {
    case ADD_NODE_COSMOS:
      if (state.includes(action.payload.id)) {
        return state;
      }
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
          repeatAlerts: cosmosRepeatAlerts,
          timeWindowAlerts: cosmosTimeWindowAlerts,
          thresholdAlerts: cosmosThresholdAlerts,
          severityAlerts: cosmosSeverityAlerts,
        },
      };
    case UPDATE_CHAIN_NAME_COSMOS:
      return {
        ...state,
        [action.payload.id]: {
          ...state[action.payload.id],
          chain_name: action.payload.chain_name,
        },
      };
    case REMOVE_CHAIN_COSMOS:
      return _.omit(state, action.payload.id);
    case ADD_NODE_COSMOS:
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
    case REMOVE_NODE_COSMOS:
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
    case LOAD_REPEAT_ALERTS_COSMOS:
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
    case LOAD_TIMEWINDOW_ALERTS_COSMOS:
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
    case LOAD_THRESHOLD_ALERTS_COSMOS:
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
    case LOAD_SEVERITY_ALERTS_COSMOS:
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

function allCosmosChains(state = [], action) {
  switch (action.type) {
    case ADD_CHAIN_COSMOS:
      if (state.includes(action.payload.id)) {
        return state;
      }
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
  CosmosNodesReducer,
  CosmosChainsReducer,
  CurrentCosmosChain,
  cosmosRepeatAlerts,
  cosmosThresholdAlerts,
  cosmosTimeWindowAlerts,
  cosmosSeverityAlerts,
};
