/* eslint-disable no-prototype-builtins */
/* eslint-disable no-param-reassign */
import _ from 'lodash';
import { combineReducers } from 'redux';
import {
  ADD_CHAIN_CHAINLINK,
  ADD_NODE_CHAINLINK,
  REMOVE_NODE_CHAINLINK,
  REMOVE_CHAIN_CHAINLINK,
  UPDATE_CHAIN_NAME_CHAINLINK,
  ADD_NODE_EVM,
  REMOVE_NODE_EVM,
  ADD_WEIWATCHERS,
  REMOVE_WEIWATCHERS,
  RESET_CHAIN_CHAINLINK,
  ADD_REPOSITORY,
  REMOVE_REPOSITORY,
  UPDATE_REPEAT_ALERT,
  UPDATE_TIMEWINDOW_ALERT,
  UPDATE_THRESHOLD_ALERT,
  UPDATE_SEVERITY_ALERT,
  LOAD_CONFIG_CHAINLINK,
  LOAD_REPEAT_ALERTS_CHAINLINK,
  LOAD_TIMEWINDOW_ALERTS_CHAINLINK,
  LOAD_THRESHOLD_ALERTS_CHAINLINK,
  LOAD_SEVERITY_ALERTS_CHAINLINK,
  ADD_DOCKER,
  REMOVE_DOCKER,
  ADD_SYSTEM,
  REMOVE_SYSTEM,
} from 'redux/actions/types';
import { WARNING, INFO, CRITICAL } from 'constants/constants';

const chainlinkRepeatAlerts = {
  byId: {},
  allIds: [],
};

const chainlinkThresholdAlerts = {
  byId: {
    1: {
      name: 'System is down.',
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
    2: {
      name: 'Open file descriptors increased.',
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
    3: {
      name: 'System CPU usage increased.',
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
    4: {
      name: 'System storage usage increased.',
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
    5: {
      name: 'System RAM usage increased.',
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
    6: {
      name: 'Chainlink node: Latest block height processed by node.',
      identifier: 'head_tracker_current_head',
      description: 'Keeps track of blocks processed by the node, alerts if no change over time.',
      adornment: 'Seconds',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 300,
        enabled: true,
      },
      critical: {
        threshold: 450,
        repeat: 180,
        repeat_enabled: true,
        enabled: true,
      },
      enabled: true,
    },
    7: {
      name: 'Chainlink node: New block headers not being received.',
      identifier: 'head_tracker_heads_received_total',
      description:
        'Keeps track of when the last block header was received, '
        + 'if a block header was not received after a while an alert will be raised.',
      adornment: 'Seconds',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 300,
        enabled: true,
      },
      critical: {
        threshold: 450,
        repeat: 180,
        repeat_enabled: true,
        enabled: true,
      },
      enabled: true,
    },
    8: {
      name: 'Chainlink node: ETH Balance',
      identifier: 'eth_balance_amount',
      description:
        'If the amount of ETH is less than the threshold an alert '
        + 'will be raised. This applies to all EVM networks e.g BNB.',
      adornment: 'ETH Balance',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 10,
        enabled: false,
      },
      critical: {
        threshold: 5,
        repeat: 600,
        repeat_enabled: true,
        enabled: true,
      },
      enabled: true,
    },
    9: {
      name: 'Chainlink node is down.',
      identifier: 'node_is_down',
      description:
        'All data sources for the node are unreachable therefore the node is is declared to be down.',
      adornment: 'Seconds',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 10,
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
    10: {
      name: 'Chainlink Contracts: Node did not respond in the latest round.',
      identifier: 'price_feed_not_observed',
      description:
        'If a round has ended and the node operator did not submit a '
        + 'price feed observation in that round an alert is raised.',
      adornment: 'Missed Rounds',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 3,
        enabled: true,
      },
      critical: {
        threshold: 6,
        repeat: 300,
        repeat_enabled: true,
        enabled: true,
      },
      enabled: true,
    },
    11: {
      name: "Chainlink Contracts: Node's answer deviates from the median answer.",
      identifier: 'price_feed_deviation',
      description:
        'If a round has ended and the node operator submitted a '
        + 'price feed observation that deviates from the median by a certain threshold '
        + 'an alert is raised.',
      adornment: '%',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 4,
        enabled: true,
      },
      critical: {
        threshold: 15,
        repeat: 300,
        repeat_enabled: true,
        enabled: true,
      },
      enabled: true,
    },
    12: {
      name: 'EVM Node: Node is Down.',
      identifier: 'evm_node_is_down',
      description:
        'If the EVM node is not reachable for a period of time this alert will be '
        + 'raised.',
      adornment: 'Seconds',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 300,
        enabled: true,
      },
      critical: {
        threshold: 300,
        repeat: 500,
        repeat_enabled: true,
        enabled: true,
      },
      enabled: true,
    },
    13: {
      name: 'EVM Node: block height difference between nodes.',
      identifier: 'evm_block_syncing_block_height_difference',
      description:
        'If the block height difference between monitored EVM nodes is greater '
        + 'than the specified thresholds this alert will be raised.',
      adornment: 'Blocks',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 700,
        enabled: true,
      },
      critical: {
        threshold: 1000,
        repeat: 300,
        repeat_enabled: true,
        enabled: true,
      },
      enabled: true,
    },
    14: {
      name: 'EVM Node: block height not changed after a period of time.',
      identifier: 'evm_block_syncing_no_change_in_block_height',
      description:
        'If the block height has not changed after a period of time this alert '
        + 'is raised.',
      adornment: 'Seconds',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 300,
        enabled: true,
      },
      critical: {
        threshold: 450,
        repeat: 300,
        repeat_enabled: true,
        enabled: true,
      },
      enabled: true,
    },
  },
  allIds: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14'],
};

const chainlinkTimeWindowAlerts = {
  byId: {
    15: {
      name: 'Chainlink node: Number of unconfirmed transactions.',
      identifier: 'unconfirmed_transactions',
      description:
        'Number of unconfirmed transactions per node persist over a time period. '
        + 'Example: If a node has 50 unconfirmed transactions for a period of 5 minutes you will '
        + 'get a critical alert.',
      adornment_threshold: 'Transaction Count',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 15,
        time_window: 0,
        enabled: false,
      },
      critical: {
        threshold: 50,
        time_window: 300,
        repeat: 300,
        repeat_enabled: true,
        enabled: true,
      },
      enabled: true,
    },
    16: {
      name: 'Chainlink node: Run status update total.',
      identifier: 'run_status_update_total',
      description: 'Number of jobs that have had an error over a time period.',
      adornment_threshold: 'Errors',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 50,
        time_window: 300,
        enabled: true,
      },
      critical: {
        threshold: 100,
        time_window: 300,
        repeat: 300,
        repeat_enabled: true,
        enabled: true,
      },
      enabled: true,
    },
    17: {
      name: 'Chainlink node: Max Unconfirmed Blocks.',
      identifier: 'max_unconfirmed_blocks',
      description:
        'The max number of blocks your transactions have been unconfirmed '
        + 'for over a time period above the threshold. Example: If your transactions are '
        + 'unconfirmed for 50 blocks after 5 minutes you will get a critical alert.',
      adornment_threshold: 'Block',
      adornment_time: 'Seconds',
      parent_id: '',
      warning: {
        threshold: 15,
        time_window: 300,
        enabled: true,
      },
      critical: {
        threshold: 50,
        time_window: 300,
        repeat: 300,
        repeat_enabled: true,
        enabled: true,
      },
      enabled: true,
    },
  },
  allIds: ['15', '16', '17'],
};

const chainlinkSeverityAlerts = {
  byId: {
    18: {
      name: 'Chainlink node: Node Switch',
      identifier: 'process_start_time_seconds',
      description:
        'Whenever a node being monitored goes down, a back-up Chainlink '
        + 'is started, this alert signifies that.',
      severity: WARNING,
      parent_id: '',
      enabled: true,
    },
    19: {
      name: 'Ethereum Balance Topped Up',
      identifier: 'eth_balance_amount_increase',
      description: 'Whenever the ethereum balance of a node is topped up you will get alerted.',
      severity: INFO,
      parent_id: '',
      enabled: true,
    },
    20: {
      name: "Chainlink node: Gas price increases over the node's price limit",
      identifier: 'tx_manager_gas_bump_exceeds_limit_total',
      description:
        'If the current gas price is higher than the gas limit of the node an '
        + 'alert should is raised',
      severity: CRITICAL,
      parent_id: '',
      enabled: true,
    },
    21: {
      name: 'Chainlink Contracts: Consensus Failure',
      identifier: 'consensus_failure',
      description:
        'If the number of oracles that have submitted their observations, '
        + 'is less than the minimum requirement. Severity is set as warning as from a node '
        + 'operator perspective there is nothing one can do.',
      severity: INFO,
      parent_id: '',
      enabled: true,
    },
  },
  allIds: ['18', '19', '20', '21'],
};

// Reducers to add and remove chainlink node configurations from global state
function nodesById(state = {}, action) {
  switch (action.type) {
    case ADD_NODE_CHAINLINK:
      return {
        ...state,
        [action.payload.id]: action.payload,
      };
    case REMOVE_NODE_CHAINLINK:
      return _.omit(state, action.payload.id);
    default:
      return state;
  }
}

// Reducers to add and remove from list of all chainlink nodes
function allNodes(state = [], action) {
  switch (action.type) {
    case ADD_NODE_CHAINLINK:
      if (state.includes(action.payload.id)) {
        return state;
      }
      return state.concat(action.payload.id);
    case REMOVE_NODE_CHAINLINK:
      return state.filter((config) => config !== action.payload.id);
    default:
      return state;
  }
}

const ChainlinkNodesReducer = combineReducers({
  byId: nodesById,
  allIds: allNodes,
});

// Reducers to add and remove evm node configurations from global state
function evmNodesById(state = {}, action) {
  switch (action.type) {
    case ADD_NODE_EVM:
      return {
        ...state,
        [action.payload.id]: action.payload,
      };
    case REMOVE_NODE_EVM:
      return _.omit(state, action.payload.id);
    default:
      return state;
  }
}

// Reducers to add and remove from list of all evm nodes
function allEvmNodes(state = [], action) {
  switch (action.type) {
    case ADD_NODE_EVM:
      if (state.includes(action.payload.id)) {
        return state;
      }
      return state.concat(action.payload.id);
    case REMOVE_NODE_EVM:
      return state.filter((config) => config !== action.payload.id);
    default:
      return state;
  }
}

const EvmNodesReducer = combineReducers({
  byId: evmNodesById,
  allIds: allEvmNodes,
});

const weiWatchersData = {
  parent_id: '',
  weiwatchers_url: '',
  monitor_contract: false,
  network_name: '',
};

function chainlinkChainsById(state = {}, action) {
  switch (action.type) {
    case ADD_CHAIN_CHAINLINK:
      if (state[action.payload.id] !== undefined) {
        return state;
      }
      return {
        ...state,
        [action.payload.id]: {
          id: action.payload.id,
          chain_name: action.payload.chain_name,
          nodes: [],
          evmNodes: [],
          weiWatchers: weiWatchersData,
          githubRepositories: [],
          dockerHubs: [],
          systems: [],
          repeatAlerts: chainlinkRepeatAlerts,
          timeWindowAlerts: chainlinkTimeWindowAlerts,
          thresholdAlerts: chainlinkThresholdAlerts,
          severityAlerts: chainlinkSeverityAlerts,
        },
      };
    case UPDATE_CHAIN_NAME_CHAINLINK:
      return {
        ...state,
        [action.payload.id]: {
          ...state[action.payload.id],
          chain_name: action.payload.chain_name,
        },
      };
    case REMOVE_CHAIN_CHAINLINK:
      return _.omit(state, action.payload.id);
    case ADD_NODE_CHAINLINK:
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
    case REMOVE_NODE_CHAINLINK:
      return {
        ...state,
        [action.payload.parent_id]: {
          ...state[action.payload.parent_id],
          nodes: state[action.payload.parent_id].nodes.filter(
            (config) => config !== action.payload.id,
          ),
        },
      };
    case ADD_NODE_EVM:
      if (state[action.payload.parent_id].evmNodes.includes(action.payload.id)) {
        return state;
      }
      return {
        ...state,
        [action.payload.parent_id]: {
          ...state[action.payload.parent_id],
          evmNodes: state[action.payload.parent_id].evmNodes.concat(action.payload.id),
        },
      };
    case REMOVE_NODE_EVM:
      return {
        ...state,
        [action.payload.parent_id]: {
          ...state[action.payload.parent_id],
          evmNodes: state[action.payload.parent_id].evmNodes.filter(
            (config) => config !== action.payload.id,
          ),
        },
      };
    case ADD_WEIWATCHERS:
      return {
        ...state,
        [action.payload.parent_id]: {
          ...state[action.payload.parent_id],
          weiWatchers: action.payload,
        },
      };
    case REMOVE_WEIWATCHERS:
      return {
        ...state,
        [action.payload.parent_id]: {
          ...state[action.payload.parent_id],
          weiWatchers: weiWatchersData,
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
    case ADD_SYSTEM:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (state[action.payload.parent_id] === undefined) {
        return state;
      }
      if (state[action.payload.parent_id].systems.includes(action.payload.id)) {
        return state;
      }
      return {
        ...state,
        [action.payload.parent_id]: {
          ...state[action.payload.parent_id],
          systems: state[action.payload.parent_id].systems.concat(action.payload.id),
        },
      };
    case REMOVE_SYSTEM:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (state[action.payload.parent_id] === undefined) {
        return state;
      }
      return {
        ...state,
        [action.payload.parent_id]: {
          ...state[action.payload.parent_id],
          systems: state[action.payload.parent_id].systems.filter(
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
    case LOAD_REPEAT_ALERTS_CHAINLINK:
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
    case LOAD_TIMEWINDOW_ALERTS_CHAINLINK:
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
    case LOAD_THRESHOLD_ALERTS_CHAINLINK:
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
    case LOAD_SEVERITY_ALERTS_CHAINLINK:
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

function allChainlinkChains(state = [], action) {
  switch (action.type) {
    case ADD_CHAIN_CHAINLINK:
      if (state.includes(action.payload.id)) {
        return state;
      }
      return state.concat(action.payload.id);
    case REMOVE_CHAIN_CHAINLINK:
      return state.filter((config) => config !== action.payload.id);
    default:
      return state;
  }
}

const ChainlinkChainsReducer = combineReducers({
  byId: chainlinkChainsById,
  allIds: allChainlinkChains,
});

function CurrentChainlinkChain(state = '', action) {
  switch (action.type) {
    case ADD_CHAIN_CHAINLINK:
      return action.payload.id;
    case RESET_CHAIN_CHAINLINK:
      return '';
    case LOAD_CONFIG_CHAINLINK:
      return action.payload.id;
    default:
      return state;
  }
}

export {
  ChainlinkNodesReducer,
  EvmNodesReducer,
  ChainlinkChainsReducer,
  CurrentChainlinkChain,
  chainlinkRepeatAlerts,
  chainlinkThresholdAlerts,
  chainlinkTimeWindowAlerts,
  chainlinkSeverityAlerts,
};
