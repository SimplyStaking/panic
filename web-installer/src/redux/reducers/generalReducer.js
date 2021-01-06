import _ from 'lodash';
import { combineReducers } from 'redux';
import {
  UPDATE_PERIODIC,
  ADD_REPOSITORY,
  ADD_SYSTEM,
  REMOVE_REPOSITORY,
  REMOVE_SYSTEM,
  ADD_KMS,
  REMOVE_KMS,
  UPDATE_THRESHOLD_ALERT,
  UPDATE_REPEAT_ALERT,
  LOAD_REPOSITORY,
  LOAD_SYSTEM,
  LOAD_KMS,
  LOAD_REPOSITORY_GENERAL,
  LOAD_SYSTEM_GENERAL,
  LOAD_REPEAT_ALERTS_GENERAL,
  LOAD_THRESHOLD_ALERTS_GENERAL,
} from 'redux/actions/types';
import { GLOBAL } from 'constants/constants';

const generalThresholdAlerts = {
  byId: {
    1: {
      name: 'Open File Descriptors Increased',
      identifier: 'open_file_descriptors',
      description:
        'Open File Descriptors alerted on based on percentage usage .',
      adornment: '%',
      adornment_time: 'Seconds',
      parent_id: 'GLOBAL',
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
    2: {
      name: 'System CPU Usage Increased',
      identifier: 'system_cpu_usage',
      description: 'System CPU alerted on based on percentage usage.',
      adornment: '%',
      adornment_time: 'Seconds',
      parent_id: 'GLOBAL',
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
    3: {
      name: 'System storage usage increased',
      identifier: 'system_storage_usage',
      description: 'System Storage alerted on based on percentage usage.',
      adornment: '%',
      adornment_time: 'Seconds',
      parent_id: 'GLOBAL',
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
    4: {
      name: 'System RAM usage increased',
      identifier: 'system_ram_usage',
      description: 'System RAM alerted on based on percentage usage.',
      adornment: '%',
      adornment_time: 'Seconds',
      parent_id: 'GLOBAL',
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
  allIds: ['1', '2', '3', '4'],
};

const generalRepeatAlerts = {
  byId: {
    5: {
      name: 'System Is Down',
      identifier: 'system_is_down',
      description:
        'The Node Exporter URL is unreachable therefore the '
        + 'system is taken to be down.',
      adornment: 'Seconds',
      parent_id: 'GLOBAL',
      warning: {
        repeat: 0,
        enabled: true,
      },
      critical: {
        repeat: 300,
        enabled: true,
      },
      enabled: true,
    },
  },
  allIds: ['5'],
};

// Initial periodic state
const periodicState = {
  time: 0,
  enabled: false,
};

// Initial general state
const generalState = {
  byId: {
    GLOBAL: {
      chain_name: GLOBAL,
      id: GLOBAL,
      repositories: [],
      systems: [],
      periodic: periodicState,
      thresholdAlerts: generalThresholdAlerts,
      repeatAlerts: generalRepeatAlerts,
    },
  },
  allIds: [GLOBAL],
};

// General reducer to keep track of Periodic alive reminder, repositories and
// systems
function GeneralReducer(state = generalState, action) {
  switch (action.type) {
    case ADD_REPOSITORY:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (action.payload.parent_id !== GLOBAL) {
        return state;
      }
      if (
        // eslint-disable-next-line no-prototype-builtins
        !state.byId[action.payload.parent_id].hasOwnProperty('repositories')
      ) {
        // eslint-disable-next-line no-param-reassign
        state.byId[action.payload.parent_id].repositories = [];
      }
      return {
        ...state,
        byId: {
          ...state.byId,
          GLOBAL: {
            ...state.byId[GLOBAL],
            repositories: state.byId[GLOBAL].repositories.concat(
              action.payload.id,
            ),
          },
        },
      };
    case LOAD_REPOSITORY_GENERAL:
      if (!state.byId[GLOBAL].repositories.includes(action.payload.id)) {
        return {
          ...state,
          byId: {
            ...state.byId,
            GLOBAL: {
              ...state.byId[GLOBAL],
              repositories: state.byId[GLOBAL].repositories.concat(
                action.payload.id,
              ),
            },
          },
        };
      }
      return state;

    case REMOVE_REPOSITORY:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (action.payload.parent_id !== GLOBAL) {
        return state;
      }
      return {
        ...state,
        byId: {
          ...state.byId,
          GLOBAL: {
            ...state.byId[GLOBAL],
            repositories: state.byId[GLOBAL].repositories.filter(
              (config) => config !== action.payload.id,
            ),
          },
        },
      };
    case ADD_SYSTEM:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (action.payload.parent_id !== GLOBAL) {
        return state;
      }
      return {
        ...state,
        byId: {
          ...state.byId,
          GLOBAL: {
            ...state.byId[GLOBAL],
            systems: state.byId[GLOBAL].systems.concat(action.payload.id),
          },
        },
      };
    case LOAD_SYSTEM_GENERAL:
      if (
        !state.byId[action.payload.parent_id].systems.includes(
          action.payload.id,
        )
      ) {
        return {
          ...state,
          byId: {
            ...state.byId,
            GLOBAL: {
              ...state.byId[GLOBAL],
              systems: state.byId[GLOBAL].systems.concat(action.payload.id),
            },
          },
        };
      }
      return state;

    case REMOVE_SYSTEM:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (action.payload.parent_id !== GLOBAL) {
        return state;
      }

      return {
        ...state,
        byId: {
          ...state.byId,
          GLOBAL: {
            ...state.byId[GLOBAL],
            systems: state.byId[GLOBAL].systems.filter(
              (config) => config !== action.payload.id,
            ),
          },
        },
      };
    case UPDATE_REPEAT_ALERT:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (action.payload.parent_id !== GLOBAL) {
        return state;
      }
      return {
        ...state,
        byId: {
          ...state.byId,
          GLOBAL: {
            ...state.byId[GLOBAL],
            repeatAlerts: {
              ...state.byId[GLOBAL].repeatAlerts,
              byId: {
                ...state.byId[GLOBAL].repeatAlerts.byId,
                [action.payload.id]: action.payload.alert,
              },
            },
          },
        },
      };
    case LOAD_REPEAT_ALERTS_GENERAL:
      return {
        ...state,
        byId: {
          ...state.byId,
          GLOBAL: {
            ...state.byId[GLOBAL],
            repeatAlerts: action.payload.alerts,
          },
        },
      };
    case UPDATE_THRESHOLD_ALERT:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (action.payload.parent_id !== GLOBAL) {
        return state;
      }
      return {
        ...state,
        byId: {
          ...state.byId,
          GLOBAL: {
            ...state.byId[GLOBAL],
            thresholdAlerts: {
              ...state.byId[GLOBAL].thresholdAlerts,
              byId: {
                ...state.byId[GLOBAL].thresholdAlerts.byId,
                [action.payload.id]: action.payload.alert,
              },
            },
          },
        },
      };
    case LOAD_THRESHOLD_ALERTS_GENERAL:
      return {
        ...state,
        byId: {
          ...state.byId,
          GLOBAL: {
            ...state.byId[GLOBAL],
            thresholdAlerts: action.payload.alerts,
          },
        },
      };
    default:
      return state;
  }
}

// Periodic alive reminder reducer
function PeriodicReducer(state = periodicState, action) {
  switch (action.type) {
    case UPDATE_PERIODIC:
      return action.payload;
    default:
      return state;
  }
}

// Reducers to add and remove repository configurations from global state
function repositoriesById(state = {}, action) {
  switch (action.type) {
    case ADD_REPOSITORY:
      return {
        ...state,
        [action.payload.id]: action.payload,
      };
    case LOAD_REPOSITORY:
      return {
        ...state,
        [action.payload.id]: action.payload,
      };
    case REMOVE_REPOSITORY:
      return _.omit(state, action.payload.id);
    default:
      return state;
  }
}

// Reducers to remove from list of all repositories
function allRepositories(state = [], action) {
  switch (action.type) {
    case ADD_REPOSITORY:
      return state.concat(action.payload.id);
    case LOAD_REPOSITORY:
      if (!state.includes(action.payload.id)) {
        return state.concat(action.payload.id);
      }
      return state;

    case REMOVE_REPOSITORY:
      return state.filter((config) => config !== action.payload.id);
    default:
      return state;
  }
}

const RepositoryReducer = combineReducers({
  byId: repositoriesById,
  allIds: allRepositories,
});

// Reducers to add and remove system configurations from global state
function systemsById(state = {}, action) {
  switch (action.type) {
    case ADD_SYSTEM:
      return {
        ...state,
        [action.payload.id]: action.payload,
      };
    case LOAD_SYSTEM:
      return {
        ...state,
        [action.payload.id]: action.payload,
      };
    case REMOVE_SYSTEM:
      return _.omit(state, action.payload.id);
    default:
      return state;
  }
}

// Reducers to remove from list of all systems
function allSystems(state = [], action) {
  switch (action.type) {
    case ADD_SYSTEM:
      return state.concat(action.payload.id);
    case LOAD_SYSTEM:
      if (!state.includes(action.payload.id)) {
        return state.concat(action.payload.id);
      }
      return state;

    case REMOVE_SYSTEM:
      return state.filter((config) => config !== action.payload.id);
    default:
      return state;
  }
}

const SystemsReducer = combineReducers({
  byId: systemsById,
  allIds: allSystems,
});

// Reducers to add and remove kms configurations from global state
function kmsesById(state = {}, action) {
  switch (action.type) {
    case ADD_KMS:
      return {
        ...state,
        [action.payload.id]: action.payload,
      };
    case LOAD_KMS:
      return {
        ...state,
        [action.payload.id]: action.payload,
      };
    case REMOVE_KMS:
      return _.omit(state, action.payload.id);
    default:
      return state;
  }
}

// Reducers to add and remove from list of all kmses
function allKmses(state = [], action) {
  switch (action.type) {
    case ADD_KMS:
      return state.concat(action.payload.id);
    case LOAD_KMS:
      if (!state.includes(action.payload.id)) {
        return state.concat(action.payload.id);
      }
      return state;

    case REMOVE_KMS:
      return state.filter((config) => config !== action.payload.id);
    default:
      return state;
  }
}

const KmsReducer = combineReducers({
  byId: kmsesById,
  allIds: allKmses,
});

export {
  RepositoryReducer,
  SystemsReducer,
  KmsReducer,
  PeriodicReducer,
  GeneralReducer,
  generalThresholdAlerts,
  generalRepeatAlerts,
};
