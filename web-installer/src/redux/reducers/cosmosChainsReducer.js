/* eslint-disable no-prototype-builtins */
/* eslint-disable no-param-reassign */
import _ from 'lodash';
import { combineReducers } from 'redux';
import { INFO, WARNING, CRITICAL } from 'constants/constants';
import {
  ADD_CHAIN_COSMOS,
  ADD_NODE_COSMOS,
  REMOVE_NODE_COSMOS,
  REMOVE_CHAIN_COSMOS,
  UPDATE_CHAIN_NAME_COSMOS,
  RESET_CHAIN_COSMOS,
  ADD_REPOSITORY,
  REMOVE_REPOSITORY,
  ADD_KMS,
  REMOVE_KMS,
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
  byId: {
    1: {
      name: 'Cannot access validator',
      identifier: 'cannot_access_validator',
      description: 'If a validator is inaccessible you will be alerted.',
      adornment: 'Seconds',
      parent_id: '',
      warning: {
        repeat: 60,
        enabled: true,
      },
      critical: {
        repeat: 300,
        enabled: true,
      },
      enabled: true,
    },
    2: {
      name: 'Cannot access node',
      identifier: 'cannot_access_node',
      description: 'If a node is inaccessible you will be alerted.',
      adornment: 'Seconds',
      parent_id: '',
      warning: {
        repeat: 300,
        enabled: true,
      },
      critical: {
        repeat: 300,
        enabled: false,
      },
      enabled: true,
    },
    3: {
      name: 'Lost connection with specific peer',
      identifier: 'lost_connection_with_peer',
      description:
        'If a node loses connection with a specific peer after some '
        + 'time you will receive an alert.',
      adornment: 'Seconds',
      parent_id: '',
      warning: {
        repeat: 300,
        enabled: true,
      },
      critical: {
        repeat: 500,
        enabled: false,
      },
      enabled: true,
    },
  },
  allIds: ['1', '2', '3'],
};

const cosmosThresholdAlerts = {
  byId: {
    4: {
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
        enabled: true,
      },
      enabled: true,
    },
    5: {
      name: 'Peer count decreased below threshold',
      identifier: 'peer_count_decreased',
      description: 'Number of peers connected to your node has decreased.',
      adornment: 'Peers',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 3,
        enabled: true,
      },
      critical: {
        threshold: 2,
        repeat: 300,
        enabled: true,
      },
      enabled: true,
    },
    6: {
      name: 'No change in block height',
      identifier: 'no_change_in_block_height',
      description: 'This alert is raised when the block height does not change after some time.',
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
        enabled: true,
      },
      enabled: true,
    },
    7: {
      name: 'Time of last activity is above threshold',
      identifier: 'time_of_last_activity',
      description:
        'Alerts will be sent based on how much time has passed '
        + 'since last pre-commit/pre-vote activity.',
      adornment: 'Seconds',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 60,
        enabled: true,
      },
      critical: {
        threshold: 180,
        repeat: 300,
        enabled: true,
      },
      enabled: true,
    },
    8: {
      name: 'Mempool Size',
      identifier: 'mempool_size',
      description: 'Alerts will be sent based on how many transactions are in the mempool.',
      adornment: 'Megabytes',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 85,
        enabled: true,
      },
      critical: {
        threshold: 95,
        repeat: 300,
        enabled: true,
      },
      enabled: true,
    },
    9: {
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
        enabled: true,
      },
      enabled: true,
    },
    10: {
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
        enabled: true,
      },
      enabled: true,
    },
    11: {
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
        enabled: true,
      },
      enabled: true,
    },
    12: {
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
        enabled: true,
      },
      enabled: true,
    },
  },
  allIds: ['4', '5', '6', '7', '8', '9', '10', '11', '12'],
};

const cosmosTimeWindowAlerts = {
  byId: {
    13: {
      name: 'Missed Blocks',
      identifier: 'missed_blocks',
      description: 'After a number of consecutive missed blocks you will receive an alert.',
      adornment_threshold: 'Blocks',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 20,
        time_window: 360,
        enabled: true,
      },
      critical: {
        threshold: 100,
        time_window: 3600,
        repeat: 300,
        enabled: true,
      },
      enabled: true,
    },
  },
  allIds: ['13'],
};

const cosmosSeverityAlerts = {
  byId: {
    14: {
      name: 'Validator inaccessible on startup',
      identifier: 'validator_inaccessible_on_startup',
      description: 'Validator was not accessible on startup.',
      severity: CRITICAL,
      parent_id: '',
      enabled: true,
    },
    15: {
      name: 'Node inaccessible on startup',
      identifier: 'node_inaccessible_on_startup',
      description: 'Node was not accessible on startup.',
      severity: WARNING,
      parent_id: '',
      enabled: true,
    },
    16: {
      name: 'Slashed',
      identifier: 'slashed',
      description: 'Occurs when your validator has been slashed.',
      severity: CRITICAL,
      parent_id: '',
      enabled: true,
    },
    17: {
      name: 'Node is syncing',
      identifier: 'node_is_syncing',
      description:
        'Occurs when your node is still catching up to the rest of '
        + 'the blockchain network in terms of block height.',
      severity: INFO,
      parent_id: '',
      enabled: true,
    },
    18: {
      name: 'Validator is not active in this session',
      identifier: 'validator_not_active_in_session',
      description:
        'Occurs when your validator is not participating in the current consensus round.',
      severity: WARNING,
      parent_id: '',
      enabled: true,
    },
    19: {
      name: 'Validator set size increased',
      identifier: 'validator_set_size_increased',
      description: 'The number of validators in the set have increased.',
      severity: INFO,
      parent_id: '',
      enabled: true,
    },
    20: {
      name: 'Validator set size decreased',
      identifier: 'validator_set_size_decreased',
      description: 'The number of validators in the set have decreased.',
      severity: INFO,
      parent_id: '',
      enabled: true,
    },
    21: {
      name: 'Validator Is Jailed',
      identifier: 'validator_is_jailed',
      description: 'The number of validators in the set have decreased.',
      severity: CRITICAL,
      parent_id: '',
      enabled: true,
    },
    22: {
      name: 'Voting power increased',
      identifier: 'voting_power_increased',
      description: 'Voting power of a validator has increased.',
      severity: INFO,
      parent_id: '',
      enabled: false,
    },
    23: {
      name: 'Validator power decreased',
      identifier: 'voting_power_decreased',
      description: 'Voting power of a validator has decreased.',
      severity: INFO,
      parent_id: '',
      enabled: false,
    },
    24: {
      name: 'New proposal submitted',
      identifier: 'new_proposal',
      description: 'A new proposal has been submitted.',
      severity: INFO,
      parent_id: '',
      enabled: false,
    },
    25: {
      name: 'Proposal conducted',
      identifier: 'proposal_conducted',
      description: 'A proposal has been conducted.',
      severity: INFO,
      parent_id: '',
      enabled: false,
    },
    26: {
      name: 'Delegated balance increase',
      identifier: 'delegated_balance_increase',
      description: 'The amount of tokens delegated to your validator has increased.',
      severity: INFO,
      parent_id: '',
      enabled: false,
    },
    27: {
      name: 'Delegated balance decrease',
      identifier: 'delegated_balance_decrease',
      description: 'The amount of tokens delegated to your validator has decreased.',
      severity: INFO,
      parent_id: '',
      enabled: false,
    },
  },
  allIds: ['14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27'],
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
          kmses: [],
          repositories: [],
          dockers: [],
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
      if (state[action.payload.parent_id].repositories.includes(action.payload.id)) {
        return state;
      }
      return {
        ...state,
        [action.payload.parent_id]: {
          ...state[action.payload.parent_id],
          repositories: state[action.payload.parent_id].repositories.concat(action.payload.id),
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
          repositories: state[action.payload.parent_id].repositories.filter(
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
      if (state[action.payload.parent_id].dockers.includes(action.payload.id)) {
        return state;
      }
      return {
        ...state,
        [action.payload.parent_id]: {
          ...state[action.payload.parent_id],
          dockers: state[action.payload.parent_id].dockers.concat(action.payload.id),
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
          dockers: state[action.payload.parent_id].dockers.filter(
            (config) => config !== action.payload.id,
          ),
        },
      };
    case ADD_KMS:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (state[action.payload.parent_id] === undefined) {
        return state;
      }
      if (!state[action.payload.parent_id].hasOwnProperty('kmses')) {
        state[action.payload.parent_id].kmses = [];
      }
      return {
        ...state,
        [action.payload.parent_id]: {
          ...state[action.payload.parent_id],
          kmses: state[action.payload.parent_id].kmses.concat(action.payload.id),
        },
      };
    case REMOVE_KMS:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (state[action.payload.parent_id] === undefined) {
        return state;
      }
      return {
        ...state,
        [action.payload.parent_id]: {
          ...state[action.payload.parent_id],
          kmses: state[action.payload.parent_id].kmses.filter(
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
