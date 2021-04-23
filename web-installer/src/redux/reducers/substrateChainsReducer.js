/* eslint-disable no-prototype-builtins */
/* eslint-disable no-param-reassign */
import _ from 'lodash';
import { combineReducers } from 'redux';
import { INFO, WARNING, CRITICAL } from 'constants/constants';
import {
  ADD_CHAIN_SUBSTRATE,
  ADD_NODE_SUBSTRATE,
  REMOVE_NODE_SUBSTRATE,
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

const substrateTimeWindowAlerts = {
  byId: {
    4: {
      name: 'No change in best block height above threshold',
      identifier: 'no_change_in_best_block_height',
      description: "There hasn't been a change in best block height after some time.",
      adornment_threshold: 'Blocks',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 30,
        time_window: 360,
        enabled: true,
      },
      critical: {
        threshold: 60,
        time_window: 3600,
        enabled: true,
      },
      enabled: true,
    },
    5: {
      name: 'No change in finalized block height above threshold',
      identifier: 'no_change_in_finalized_block_height',
      description: "There hasn't been a change in finalized block height after some time.",
      adornment_threshold: 'Blocks',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 30,
        time_window: 360,
        enabled: true,
      },
      critical: {
        threshold: 60,
        time_window: 3600,
        enabled: true,
      },
      enabled: true,
    },
  },
  allIds: ['4', '5'],
};

const substrateThresholdAlerts = {
  byId: {
    6: {
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
        enabled: true,
      },
      enabled: true,
    },
    10: {
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
  allIds: ['6', '7', '8', '9', '10', '11', '12'],
};

const substrateSeverityAlerts = {
  byId: {
    13: {
      name: 'Validator inaccessible on startup',
      identifier: 'validator_inaccessible_on_startup',
      description: 'Validator was not accessible on startup.',
      severity: CRITICAL,
      parent_id: '',
      enabled: true,
    },
    14: {
      name: 'Node inaccessible on startup',
      identifier: 'node_inaccessible_on_startup',
      description: 'Node was not accessible on startup.',
      severity: WARNING,
      parent_id: '',
      enabled: true,
    },
    15: {
      name: 'Slashed',
      identifier: 'slashed',
      description: 'Occurs when your validator has been slashed.',
      severity: CRITICAL,
      parent_id: '',
      enabled: true,
    },
    16: {
      name: 'Node is syncing',
      identifier: 'node_is_syncing',
      description:
        'Occurs when your node is still catching up to the rest of '
        + 'the blockchain network in terms of block height.',
      severity: WARNING,
      parent_id: '',
      enabled: true,
    },
    17: {
      name: 'Validator is not active in this session',
      identifier: 'validator_not_active_in_session',
      description:
        'Occurs when your validator is not participating in the current consensus round.',
      severity: WARNING,
      parent_id: '',
      enabled: true,
    },
    18: {
      name: 'Validator set size increased',
      identifier: 'validator_set_size_increased',
      description: 'The number of validators in the set have increased.',
      severity: INFO,
      parent_id: '',
      enabled: true,
    },
    19: {
      name: 'Validator set size decreased',
      identifier: 'validator_set_size_decreased',
      description: 'The number of validators in the set have decreased.',
      severity: INFO,
      parent_id: '',
      enabled: true,
    },
    20: {
      name: 'Validator declared offline',
      identifier: 'validator_declared_offline',
      description: 'The validator has been declared offline by the blockchain.',
      severity: WARNING,
      parent_id: '',
      enabled: true,
    },
    21: {
      name: 'Validator not authoring',
      identifier: 'validator_not_authoring',
      description:
        'The Validator did not author a block and sent no heartbeats in the previous session',
      severity: WARNING,
      parent_id: '',
      enabled: false,
    },
    22: {
      name: 'A new payout is pending',
      identifier: 'new_payout_pending',
      description: 'A new pending payout has been detected',
      severity: WARNING,
      parent_id: '',
      enabled: false,
    },
    23: {
      name: 'New proposal submitted',
      identifier: 'new_proposal',
      description: 'A new proposal has been submitted.',
      severity: INFO,
      parent_id: '',
      enabled: false,
    },
    24: {
      name: 'Proposal conducted',
      identifier: 'proposal_conducted',
      description: 'A proposal has been conducted.',
      severity: INFO,
      parent_id: '',
      enabled: false,
    },
    25: {
      name: 'Delegated balance increase',
      identifier: 'delegated_balance_increase',
      description: 'The amount of tokens delegated to your validator has increased.',
      severity: INFO,
      parent_id: '',
      enabled: false,
    },
    26: {
      name: 'Delegated balance decrease',
      identifier: 'delegated_balance_decrease',
      description: 'The amount of tokens delegated to your validator has decreased.',
      severity: INFO,
      parent_id: '',
      enabled: false,
    },
    27: {
      name: 'Bonded balance increased',
      identifier: 'bonded_balance_increased',
      description: 'Bonded balance of your validator has increased.',
      severity: INFO,
      parent_id: '',
      enabled: false,
    },
    28: {
      name: 'Bonded balance decreased',
      identifier: 'bonded_balance_decreased',
      description: 'Bonded balance of your validator has decreased.',
      severity: INFO,
      parent_id: '',
      enabled: false,
    },
    29: {
      name: 'Free balance increased',
      identifier: 'free_balance_increased',
      description: 'Free balance of your validator has increased.',
      severity: INFO,
      parent_id: '',
      enabled: false,
    },
    30: {
      name: 'Free balance decreased',
      identifier: 'free_balance_decreased',
      description: 'Free balance of your validator has decreased.',
      severity: INFO,
      parent_id: '',
      enabled: false,
    },
    31: {
      name: 'Reserved balance increased',
      identifier: 'reserve_balance_increased',
      description: 'Reserve balance of your validator has increased.',
      severity: INFO,
      parent_id: '',
      enabled: false,
    },
    32: {
      name: 'Reserved balance decreased',
      identifier: 'reserve_balance_decreased',
      description: 'Reserve balance of your validator has decreased.',
      severity: INFO,
      parent_id: '',
      enabled: false,
    },
    33: {
      name: 'Nominated balance increased',
      identifier: 'nominated_balance_increased',
      description: 'Nominated balance of your validator has increased.',
      severity: INFO,
      parent_id: '',
      enabled: false,
    },
    34: {
      name: 'Nominated balance decreased',
      identifier: 'nominated_balance_decreased',
      description: 'Nominated balance of your validator has decreased.',
      severity: INFO,
      parent_id: '',
      enabled: false,
    },
    35: {
      name: 'Validator is not elected',
      identifier: 'validator_not_elected',
      description: 'The Validator has not been elected for the next session.',
      severity: WARNING,
      parent_id: '',
      enabled: true,
    },
    36: {
      name: 'Validator has been disabled',
      identifier: 'validator_is_disabled',
      description: 'The Validator has not been elected for the next session.',
      severity: CRITICAL,
      parent_id: '',
      enabled: true,
    },
    37: {
      name: 'New Council proposal',
      identifier: 'new_council_proposal',
      description: 'A new council proposal has been detected.',
      severity: INFO,
      parent_id: '',
      enabled: true,
    },
    38: {
      name: 'Validator is in council',
      identifier: 'validator_in_council',
      description: 'The Validator is now part of the council.',
      severity: INFO,
      parent_id: '',
      enabled: true,
    },
    39: {
      name: 'Validator not in council',
      identifier: 'validator_not_in_council',
      description: 'The Validator is no longer part of the council.',
      severity: INFO,
      parent_id: '',
      enabled: true,
    },
    40: {
      name: 'New treasury proposal',
      identifier: 'new_treasury_proposal',
      description: 'A new treasury proposal has been submitted.',
      severity: INFO,
      parent_id: '',
      enabled: true,
    },
    41: {
      name: 'New TIP proposal',
      identifier: 'new_tip_proposal',
      description: 'A new tip proposal has been submitted.',
      severity: INFO,
      parent_id: '',
      enabled: true,
    },
    42: {
      name: 'New Referendum',
      identifier: 'new_referendum',
      description: 'A new referendum has been submitted.',
      severity: INFO,
      parent_id: '',
      enabled: true,
    },
    43: {
      name: 'Referendum completed',
      identifier: 'referendum_completed',
      description: 'A new referendum has been completed.',
      severity: INFO,
      parent_id: '',
      enabled: true,
    },
  },
  allIds: [
    '13',
    '14',
    '15',
    '16',
    '17',
    '18',
    '19',
    '20',
    '21',
    '22',
    '23',
    '24',
    '25',
    '26',
    '27',
    '28',
    '29',
    '30',
    '31',
    '32',
    '33',
    '34',
    '35',
    '36',
    '37',
    '38',
    '39',
    '40',
    '41',
    '42',
    '43',
  ],
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
      return {
        ...state,
        [action.payload.id]: {
          id: action.payload.id,
          chain_name: action.payload.chain_name,
          nodes: [],
          repositories: [],
          dockers: [],
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
      if (!state.hasOwnProperty(action.payload.parent_id)) {
        state[action.payload.parent_id] = {};
      }
      if (!state[action.payload.parent_id].hasOwnProperty('repeatAlerts')) {
        state[action.payload.parent_id].repeatAlerts = {};
        state[action.payload.parent_id].chain_name = action.payload.chain_name;
        state[action.payload.parent_id].id = action.payload.parent_id;
      }
      if (!state[action.payload.parent_id].hasOwnProperty('repositories')) {
        state[action.payload.parent_id].repositories = [];
      }
      if (!state[action.payload.parent_id].hasOwnProperty('nodes')) {
        state[action.payload.parent_id].nodes = [];
      }
      if (!state[action.payload.parent_id].hasOwnProperty('timeWindowAlerts')) {
        state[action.payload.parent_id].timeWindowAlerts = substrateTimeWindowAlerts;
      }
      if (!state[action.payload.parent_id].hasOwnProperty('thresholdAlerts')) {
        state[action.payload.parent_id].thresholdAlerts = substrateThresholdAlerts;
      }
      if (!state[action.payload.parent_id].hasOwnProperty('severityAlerts')) {
        state[action.payload.parent_id].severityAlerts = substrateSeverityAlerts;
      }
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
      if (!state.hasOwnProperty(action.payload.parent_id)) {
        state[action.payload.parent_id] = {};
      }
      if (!state[action.payload.parent_id].hasOwnProperty('timeWindowAlerts')) {
        state[action.payload.parent_id].timeWindowAlerts = {};
        state[action.payload.parent_id].chain_name = action.payload.chain_name;
        state[action.payload.parent_id].id = action.payload.parent_id;
      }
      if (!state[action.payload.parent_id].hasOwnProperty('repositories')) {
        state[action.payload.parent_id].repositories = [];
      }
      if (!state[action.payload.parent_id].hasOwnProperty('nodes')) {
        state[action.payload.parent_id].nodes = [];
      }
      if (!state[action.payload.parent_id].hasOwnProperty('repeatAlerts')) {
        state[action.payload.parent_id].repeatAlerts = substrateRepeatAlerts;
      }
      if (!state[action.payload.parent_id].hasOwnProperty('thresholdAlerts')) {
        state[action.payload.parent_id].thresholdAlerts = substrateThresholdAlerts;
      }
      if (!state[action.payload.parent_id].hasOwnProperty('severityAlerts')) {
        state[action.payload.parent_id].severityAlerts = substrateSeverityAlerts;
      }
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
      if (!state.hasOwnProperty(action.payload.parent_id)) {
        state[action.payload.parent_id] = {};
      }
      if (!state[action.payload.parent_id].hasOwnProperty('thresholdAlerts')) {
        state[action.payload.parent_id].thresholdAlerts = {};
        state[action.payload.parent_id].chain_name = action.payload.chain_name;
        state[action.payload.parent_id].id = action.payload.parent_id;
      }
      if (!state[action.payload.parent_id].hasOwnProperty('repositories')) {
        state[action.payload.parent_id].repositories = [];
      }
      if (!state[action.payload.parent_id].hasOwnProperty('nodes')) {
        state[action.payload.parent_id].nodes = [];
      }
      if (!state[action.payload.parent_id].hasOwnProperty('repeatAlerts')) {
        state[action.payload.parent_id].repeatAlerts = substrateRepeatAlerts;
      }
      if (!state[action.payload.parent_id].hasOwnProperty('timeWindowAlerts')) {
        state[action.payload.parent_id].timeWindowAlerts = substrateTimeWindowAlerts;
      }
      if (!state[action.payload.parent_id].hasOwnProperty('severityAlerts')) {
        state[action.payload.parent_id].severityAlerts = substrateSeverityAlerts;
      }
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
      if (!state.hasOwnProperty(action.payload.parent_id)) {
        state[action.payload.parent_id] = {};
      }
      if (!state[action.payload.parent_id].hasOwnProperty('severityAlerts')) {
        state[action.payload.parent_id].severityAlerts = {};
        state[action.payload.parent_id].chain_name = action.payload.chain_name;
        state[action.payload.parent_id].id = action.payload.parent_id;
      }
      if (!state[action.payload.parent_id].hasOwnProperty('repositories')) {
        state[action.payload.parent_id].repositories = [];
      }
      if (!state[action.payload.parent_id].hasOwnProperty('nodes')) {
        state[action.payload.parent_id].nodes = [];
      }
      if (!state[action.payload.parent_id].hasOwnProperty('repeatAlerts')) {
        state[action.payload.parent_id].repeatAlerts = substrateRepeatAlerts;
      }
      if (!state[action.payload.parent_id].hasOwnProperty('timeWindowAlerts')) {
        state[action.payload.parent_id].timeWindowAlerts = substrateTimeWindowAlerts;
      }
      if (!state[action.payload.parent_id].hasOwnProperty('thresholdAlerts')) {
        state[action.payload.parent_id].thresholdAlerts = substrateThresholdAlerts;
      }
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
