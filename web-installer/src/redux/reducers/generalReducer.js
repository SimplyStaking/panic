import _ from 'lodash';
import { combineReducers } from 'redux';
import {
  UPDATE_PERIODIC,
  ADD_REPOSITORY,
  ADD_SYSTEM,
  REMOVE_REPOSITORY,
  REMOVE_SYSTEM,
  UPDATE_THRESHOLD_ALERT,
  LOAD_THRESHOLD_ALERTS_GENERAL,
  ADD_DOCKER,
  REMOVE_DOCKER,
} from 'redux/actions/types';
import { GENERAL } from 'constants/constants';

const generalThresholdAlerts = {
  byId: {
    1: {
      name: 'Open File Descriptors Increased',
      identifier: 'open_file_descriptors',
      description:
        'Open File Descriptors alerted on based on percentage usage .',
      adornment: '%',
      adornment_time: 'Seconds',
      parent_id: GENERAL,
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
    2: {
      name: 'System CPU Usage Increased',
      identifier: 'system_cpu_usage',
      description: 'System CPU alerted on based on percentage usage.',
      adornment: '%',
      adornment_time: 'Seconds',
      parent_id: GENERAL,
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
      name: 'System storage usage increased',
      identifier: 'system_storage_usage',
      description: 'System Storage alerted on based on percentage usage.',
      adornment: '%',
      adornment_time: 'Seconds',
      parent_id: GENERAL,
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
      name: 'System RAM usage increased',
      identifier: 'system_ram_usage',
      description: 'System RAM alerted on based on percentage usage.',
      adornment: '%',
      adornment_time: 'Seconds',
      parent_id: GENERAL,
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
      name: 'System Is Down',
      identifier: 'system_is_down',
      description:
        'The Node Exporter URL is unreachable therefore the '
        + 'system is taken to be down.',
      adornment: 'Seconds',
      adornment_time: 'Seconds',
      parent_id: GENERAL,
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
  },
  allIds: ['1', '2', '3', '4', '5'],
};

const generalRepeatAlerts = {
  byId: {},
  allIds: [],
};

const generalTimeWindowAlerts = {
  byId: {},
  allIds: [],
};

const generalSeverityAlerts = {
  byId: {},
  allIds: [],
};

// Initial periodic state
const periodicState = {
  time: 0,
  enabled: false,
};

// Initial general state
const generalState = {
  byId: {
    GENERAL: {
      chain_name: GENERAL,
      id: GENERAL,
      githubRepositories: [],
      dockerHubs: [],
      systems: [],
      periodic: periodicState,
      thresholdAlerts: generalThresholdAlerts,
      repeatAlerts: generalRepeatAlerts,
      timeWindowAlerts: generalTimeWindowAlerts,
      severityAlerts: generalSeverityAlerts,
    },
  },
  allIds: [GENERAL],
};

// General reducer to keep track of Periodic alive reminder, githubRepositories and
// systems
function GeneralReducer(state = generalState, action) {
  switch (action.type) {
    case ADD_REPOSITORY:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (action.payload.parent_id !== GENERAL) {
        return state;
      }
      if (state.byId[GENERAL].githubRepositories.includes(action.payload.id)) {
        return state;
      }
      return {
        ...state,
        byId: {
          ...state.byId,
          GENERAL: {
            ...state.byId[GENERAL],
            githubRepositories: state.byId[GENERAL].githubRepositories.concat(
              action.payload.id,
            ),
          },
        },
      };
    case REMOVE_REPOSITORY:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (action.payload.parent_id !== GENERAL) {
        return state;
      }
      return {
        ...state,
        byId: {
          ...state.byId,
          GENERAL: {
            ...state.byId[GENERAL],
            githubRepositories: state.byId[GENERAL].githubRepositories.filter(
              (config) => config !== action.payload.id,
            ),
          },
        },
      };
    case ADD_DOCKER:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (action.payload.parent_id !== GENERAL) {
        return state;
      }
      if (state.byId[GENERAL].dockerHubs.includes(action.payload.id)) {
        return state;
      }
      return {
        ...state,
        byId: {
          ...state.byId,
          GENERAL: {
            ...state.byId[GENERAL],
            dockerHubs: state.byId[GENERAL].dockerHubs.concat(
              action.payload.id,
            ),
          },
        },
      };
    case REMOVE_DOCKER:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (action.payload.parent_id !== GENERAL) {
        return state;
      }
      return {
        ...state,
        byId: {
          ...state.byId,
          GENERAL: {
            ...state.byId[GENERAL],
            dockerHub: state.byId[GENERAL].dockerHub.filter(
              (config) => config !== action.payload.id,
            ),
          },
        },
      };
    case ADD_SYSTEM:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (action.payload.parent_id !== GENERAL) {
        return state;
      }
      if (state.byId[GENERAL].systems.includes(action.payload.id)) {
        return state;
      }
      return {
        ...state,
        byId: {
          ...state.byId,
          GENERAL: {
            ...state.byId[GENERAL],
            systems: state.byId[GENERAL].systems.concat(action.payload.id),
          },
        },
      };
    case REMOVE_SYSTEM:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (action.payload.parent_id !== GENERAL) {
        return state;
      }

      return {
        ...state,
        byId: {
          ...state.byId,
          GENERAL: {
            ...state.byId[GENERAL],
            systems: state.byId[GENERAL].systems.filter(
              (config) => config !== action.payload.id,
            ),
          },
        },
      };
    case UPDATE_THRESHOLD_ALERT:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (action.payload.parent_id !== GENERAL) {
        return state;
      }
      return {
        ...state,
        byId: {
          ...state.byId,
          GENERAL: {
            ...state.byId[GENERAL],
            thresholdAlerts: {
              ...state.byId[GENERAL].thresholdAlerts,
              byId: {
                ...state.byId[GENERAL].thresholdAlerts.byId,
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
          GENERAL: {
            ...state.byId[GENERAL],
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
function githubRepositoriesById(state = {}, action) {
  switch (action.type) {
    case ADD_REPOSITORY:
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

// Reducers to remove from list of all githubRepositories
// In ADD_REPOSITORY there is a check to ensure that double the repo_id isn't
// added to the list
function allGithubRepositories(state = [], action) {
  switch (action.type) {
    case ADD_REPOSITORY:
      if (state.includes(action.payload.id)) {
        return state;
      }
      return state.concat(action.payload.id);
    case REMOVE_REPOSITORY:
      return state.filter((config) => config !== action.payload.id);
    default:
      return state;
  }
}

const GitHubRepositoryReducer = combineReducers({
  byId: githubRepositoriesById,
  allIds: allGithubRepositories,
});

// Reducers to add and remove dockerHub configurations from global state
function dockerHubsById(state = {}, action) {
  switch (action.type) {
    case ADD_DOCKER:
      return {
        ...state,
        [action.payload.id]: action.payload,
      };
    case REMOVE_DOCKER:
      return _.omit(state, action.payload.id);
    default:
      return state;
  }
}

// Reducers to remove from list of all dockerHub configs
function allDockerHubs(state = [], action) {
  switch (action.type) {
    case ADD_DOCKER:
      if (state.includes(action.payload.id)) {
        return state;
      }
      return state.concat(action.payload.id);
    case REMOVE_DOCKER:
      return state.filter((config) => config !== action.payload.id);
    default:
      return state;
  }
}

const DockerHubReducer = combineReducers({
  byId: dockerHubsById,
  allIds: allDockerHubs,
});

// Reducers to add and remove system configurations from global state
function systemsById(state = {}, action) {
  switch (action.type) {
    case ADD_SYSTEM:
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
      if (state.includes(action.payload.id)) {
        return state;
      }
      return state.concat(action.payload.id);
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

export {
  GitHubRepositoryReducer,
  SystemsReducer,
  PeriodicReducer,
  GeneralReducer,
  generalThresholdAlerts,
  DockerHubReducer,
};
