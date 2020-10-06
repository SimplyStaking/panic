import _ from 'lodash';
import { combineReducers } from 'redux';
import {
  UPDATE_PERIODIC, ADD_REPOSITORY, ADD_SYSTEM, REMOVE_REPOSITORY,
  REMOVE_SYSTEM, ADD_KMS, REMOVE_KMS, ADD_TELEGRAM_CHANNEL,
  REMOVE_TELEGRAM_CHANNEL, ADD_TWILIO_CHANNEL, REMOVE_TWILIO_CHANNEL,
  ADD_EMAIL_CHANNEL, REMOVE_EMAIL_CHANNEL, ADD_OPSGENIE_CHANNEL,
  REMOVE_OPSGENIE_CHANNEL, ADD_PAGERDUTY_CHANNEL, REMOVE_PAGERDUTY_CHANNEL,
  UPDATE_THRESHOLD_ALERT,
} from '../actions/types';
import { GLOBAL } from '../../constants/constants';

const generalThresholdAlerts = {
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
    3: {
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
    4: {
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
    5: {
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
  allIds: ['1', '2', '3', '4', '5'],
};

// Initial periodic state
const periodicState = {
  periodic: {
    time: 0,
    enabled: false,
  },
};

// Initial general state
const generalState = {
  byId: {
    GLOBAL: {
      repositories: [],
      systems: [],
      periodic: periodicState,
      telegrams: [],
      twilios: [],
      emails: [],
      pagerduties: [],
      opsgenies: [],
      thresholdAlerts: generalThresholdAlerts,
    },
  },
  allIds: [GLOBAL],
};

// General reducer to keep track of Periodic alive reminder, repositories and
// systems
function GeneralReducer(state = generalState, action) {
  switch (action.type) {
    case UPDATE_PERIODIC:
      return {
        ...state,
        periodic: action.payload,
      };
    case ADD_REPOSITORY:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (action.payload.parentId !== GLOBAL) {
        return state;
      }

      return {
        ...state,
        byId: {
          ...state.byId,
          GLOBAL: {
            ...state.byId[GLOBAL],
            repositories: state.byId[GLOBAL].repositories.concat(action.payload.id),
          },
        },
      };
    case REMOVE_REPOSITORY:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (action.payload.parentId !== GLOBAL) {
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
      if (action.payload.parentId !== GLOBAL) {
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
    case REMOVE_SYSTEM:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (action.payload.parentId !== GLOBAL) {
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
    case ADD_TELEGRAM_CHANNEL:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (action.payload.parentId !== GLOBAL) {
        return state;
      }
      return {
        ...state,
        byId: {
          ...state.byId,
          GLOBAL: {
            ...state.byId[GLOBAL],
            telegrams: state.byId[GLOBAL].telegrams.concat(action.payload.id),
          },
        },
      };
    case REMOVE_TELEGRAM_CHANNEL:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (action.payload.parentId !== GLOBAL) {
        return state;
      }
      return {
        ...state,
        byId: {
          ...state.byId,
          GLOBAL: {
            ...state.byId[GLOBAL],
            telegrams: state.byId[GLOBAL].telegrams.filter(
              (config) => config !== action.payload.id,
            ),
          },
        },
      };
    case ADD_TWILIO_CHANNEL:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (action.payload.parentId !== GLOBAL) {
        return state;
      }
      return {
        ...state,
        byId: {
          ...state.byId,
          GLOBAL: {
            ...state.byId[GLOBAL],
            twilios: state.byId[GLOBAL].twilios.concat(action.payload.id),
          },
        },
      };
    case REMOVE_TWILIO_CHANNEL:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (action.payload.parentId !== GLOBAL) {
        return state;
      }
      return {
        ...state,
        byId: {
          ...state.byId,
          GLOBAL: {
            ...state.byId[GLOBAL],
            twilios: state.byId[GLOBAL].twilios.filter(
              (config) => config !== action.payload.id,
            ),
          },
        },
      };
    case ADD_EMAIL_CHANNEL:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (action.payload.parentId !== GLOBAL) {
        return state;
      }
      return {
        ...state,
        byId: {
          ...state.byId,
          GLOBAL: {
            ...state.byId[GLOBAL],
            emails: state.byId[GLOBAL].emails.concat(action.payload.id),
          },
        },
      };
    case REMOVE_EMAIL_CHANNEL:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (action.payload.parentId !== GLOBAL) {
        return state;
      }
      return {
        ...state,
        byId: {
          ...state.byId,
          GLOBAL: {
            ...state.byId[GLOBAL],
            emails: state.byId[GLOBAL].emails.filter(
              (config) => config !== action.payload.id,
            ),
          },
        },
      };
    case ADD_PAGERDUTY_CHANNEL:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (action.payload.parentId !== GLOBAL) {
        return state;
      }
      return {
        ...state,
        byId: {
          ...state.byId,
          GLOBAL: {
            ...state.byId[GLOBAL],
            pagerduties: state.byId[GLOBAL].pagerduties.concat(action.payload.id),
          },
        },
      };
    case REMOVE_PAGERDUTY_CHANNEL:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (action.payload.parentId !== GLOBAL) {
        return state;
      }
      return {
        ...state,
        byId: {
          ...state.byId,
          GLOBAL: {
            ...state.byId[GLOBAL],
            pagerduties: state.byId[GLOBAL].pagerduties.filter(
              (config) => config !== action.payload.id,
            ),
          },
        },
      };
    case ADD_OPSGENIE_CHANNEL:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (action.payload.parentId !== GLOBAL) {
        return state;
      }
      return {
        ...state,
        byId: {
          ...state.byId,
          GLOBAL: {
            ...state.byId[GLOBAL],
            opsgenies: state.byId[GLOBAL].opsgenies.concat(action.payload.id),
          },
        },
      };
    case REMOVE_OPSGENIE_CHANNEL:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (action.payload.parentId !== GLOBAL) {
        return state;
      }
      return {
        ...state,
        byId: {
          ...state.byId,
          GLOBAL: {
            ...state.byId[GLOBAL],
            opsgenies: state.byId[GLOBAL].opsgenies.filter(
              (config) => config !== action.payload.id,
            ),
          },
        },
      };
    case UPDATE_THRESHOLD_ALERT:
      // Since this is common for multiple chains and general settings
      // it must be conditional. Checking if parent id exists is enough.
      if (action.payload.parentId !== GLOBAL) {
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
  RepositoryReducer, SystemsReducer, KmsReducer, PeriodicReducer,
  GeneralReducer,
};
