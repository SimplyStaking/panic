/*
  Reference to understand this reducer code
  https://redux.js.org/recipes/structuring-reducers/refactoring-reducer-example
*/

import {
  ADD_CHAIN, ADD_NODE, ADD_REPOSITORY, REMOVE_NODE, REMOVE_REPOSITORY,
  ADD_KMS, REMOVE_KMS, SET_ALERTS, ADD_CONFIG, REMOVE_CONFIG, RESET_CONFIG,
  LOAD_CONFIG, ADD_TELEGRAM_CHANNEL, REMOVE_TELEGRAM_CHANNEL,
  ADD_OPSGENIE_CHANNEL, REMOVE_OPSGENIE_CHANNEL, ADD_EMAIL_CHANNEL,
  REMOVE_EMAIL_CHANNEL, ADD_PAGERDUTY_CHANNEL, REMOVE_PAGERDUTY_CHANNEL,
  ADD_TWILIO_CHANNEL, REMOVE_TWILIO_CHANNEL, UPDATE_WARNING_DELAY,
  UPDATE_WARNING_REPEAT, UPDATE_WARNING_THRESHOLD, UPDATE_WARNING_TIMEWINDOW,
  UPDATE_WARNING_ENABLED, UPDATE_CRITICAL_DELAY, UPDATE_CRITICAL_REPEAT,
  UPDATE_CRITICAL_THRESHOLD, UPDATE_CRITICAL_TIMEWINDOW, UPDATE_CRITICAL_ENABLED,
  UPDATE_ALERT_ENABLED, UPDATE_ALERT_SEVERTY_LEVEL, UPDATE_ALERT_SEVERTY_ENABLED,
} from '../actions/types';

import { INFO, WARNING, CRITICAL } from '../../constants/constants';

const initialstate = {
  cosmosConfigs: [],
  config: {
    chainName: '',
    nodes: [],
    repositories: [],
    kmses: [],
    channels: [],
    telegrams: [],
    emails: [],
    opsgenies: [],
    pagerduties: [],
    twilios: [],
    alerts: {
      thresholds: {
        alert1: {
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
        alert2: {
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
        alert3: {
          name: 'Lost connection with specific peer',
          warning: {
            delay: 60,
            enabled: true,
          },
          critical: {
            delay: 120,
            enabled: false,
          },
          enabled: true,
        },
        alert4: {
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
        alert5: {
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
        alert6: {
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
        alert7: {
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
        alert8: {
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
        alert9: {
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
        alert10: {
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
        alert11: {
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
        alert12: {
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
        alert13: {
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
      severties: {
        alert1: {
          name: 'Validator inaccessible on startup',
          severtiy: CRITICAL,
          enabled: true,
        },
        alert2: {
          name: 'Node inaccessible on startup',
          severtiy: WARNING,
          enabled: true,
        },
        alert3: {
          name: 'Slashed',
          severtiy: CRITICAL,
          enabled: true,
        },
        alert4: {
          name: 'Node is syncing',
          severtiy: WARNING,
          enabled: true,
        },
        alert5: {
          name: 'Validator is not active in this session',
          severtiy: WARNING,
          enabled: true,
        },
        alert6: {
          name: 'Validator set size increased',
          severtiy: INFO,
          enabled: true,
        },
        alert7: {
          name: 'Validator set size decreased',
          severtiy: INFO,
          enabled: true,
        },
        alert8: {
          name: 'Validator is jailed',
          severtiy: CRITICAL,
          enabled: true,
        },
        alert9: {
          name: 'Voting power increased',
          severtiy: INFO,
          enabled: false,
        },
        alert10: {
          name: 'Validator power decreased',
          severtiy: INFO,
          enabled: false,
        },
        alert11: {
          name: 'New proposal submitted',
          severtiy: INFO,
          enabled: false,
        },
        alert12: {
          name: 'Proposal conducted',
          severtiy: INFO,
          enabled: false,
        },
        alert13: {
          name: 'Delegated balance increase',
          severtiy: INFO,
          enabled: false,
        },
        alert14: {
          name: 'Delegagted balance decrease',
          severtiy: INFO,
          enabled: false,
        },
      },
    },
  },
};

function chainsReducer(state = initialstate, action) {
  switch (action.type) {
    case ADD_CHAIN:
      return {
        ...state,
        config: {
          ...state.config,
          chainName: action.payload.chainName,
        },
      };
    case ADD_NODE:
      return {
        ...state,
        config: {
          ...state.config,
          nodes: state.config.nodes.concat(action.payload),
        },
      };
    case REMOVE_NODE:
      return {
        ...state,
        config: {
          ...state.config,
          nodes: state.config.nodes.filter((node) => node !== action.payload),
        },
      };
    case ADD_REPOSITORY:
      return {
        ...state,
        config: {
          ...state.config,
          repositories: state.config.repositories.concat(action.payload),
        },
      };
    case REMOVE_REPOSITORY:
      return {
        ...state,
        config: {
          ...state.config,
          repositories: state.config.repositories.filter(
            (repository) => repository !== action.payload,
          ),
        },
      };
    case ADD_KMS:
      return {
        ...state,
        config: {
          ...state.config,
          kmses: state.config.kmses.concat(action.payload),
        },
      };
    case REMOVE_KMS:
      return {
        ...state,
        config: {
          ...state.config,
          kmses: state.config.kmses.filter(
            (kms) => kms !== action.payload,
          ),
        },
      };
    case ADD_TELEGRAM_CHANNEL:
      return {
        ...state,
        config: {
          ...state.config,
          telegrams: state.config.telegrams.concat(action.payload),
        },
      };
    case REMOVE_TELEGRAM_CHANNEL:
      return {
        ...state,
        config: {
          ...state.config,
          telegrams: state.config.telegrams.filter(
            (telegram) => telegram !== action.payload,
          ),
        },
      };
    case ADD_OPSGENIE_CHANNEL:
      return {
        ...state,
        config: {
          ...state.config,
          opsgenies: state.config.opsgenies.concat(action.payload),
        },
      };
    case REMOVE_OPSGENIE_CHANNEL:
      return {
        ...state,
        config: {
          ...state.config,
          opsgenies: state.config.opsgenies.filter(
            (opsgenie) => opsgenie !== action.payload,
          ),
        },
      };
    case ADD_EMAIL_CHANNEL:
      return {
        ...state,
        config: {
          ...state.config,
          emails: state.config.emails.concat(action.payload),
        },
      };
    case REMOVE_EMAIL_CHANNEL:
      return {
        ...state,
        config: {
          ...state.config,
          emails: state.config.emails.filter(
            (email) => email !== action.payload,
          ),
        },
      };
    case ADD_TWILIO_CHANNEL:
      return {
        ...state,
        config: {
          ...state.config,
          twilios: state.config.twilios.concat(action.payload),
        },
      };
    case REMOVE_TWILIO_CHANNEL:
      return {
        ...state,
        config: {
          ...state.config,
          twilios: state.config.twilios.filter(
            (twilio) => twilio !== action.payload,
          ),
        },
      };
    case ADD_PAGERDUTY_CHANNEL:
      return {
        ...state,
        config: {
          ...state.config,
          pagerduties: state.config.pagerduties.concat(action.payload),
        },
      };
    case REMOVE_PAGERDUTY_CHANNEL:
      return {
        ...state,
        config: {
          ...state.config,
          pagerduties: state.config.pagerduties.filter(
            (pagerduty) => pagerduty !== action.payload,
          ),
        },
      };
    case SET_ALERTS:
      return {
        ...state,
        config: {
          ...state.config,
          alerts: action.payload.alerts,
        },
      };
    case ADD_CONFIG:
      return {
        ...state,
        cosmosConfigs: state.cosmosConfigs.concat(state.config),
      };
    case REMOVE_CONFIG:
      return {
        ...state,
        cosmosConfigs: state.cosmosConfigs.filter(
          (cosmosConfig) => cosmosConfig !== action.payload,
        ),
      };
    case RESET_CONFIG:
      return {
        ...state,
        config: initialstate.config,
      };
    case LOAD_CONFIG:
      return {
        ...state,
        config: state.cosmosConfigs.filter(
          (cosmosConfig) => cosmosConfig === action.payload,
        )[0],
      };
    case UPDATE_WARNING_DELAY:
      return {
        ...state,
        config: {
          ...state.config,
          alerts: {
            ...state.config.alerts,
            thresholds: {
              ...state.config.alerts.thresholds,
              [action.payload.alertID]: {
                ...state.config.alerts.thresholds[action.payload.alertID],
                warning: {
                  ...state.config.alerts.thresholds[action.payload.alertID].warning,
                  delay: action.payload.delay,
                },
              },
            },
          },
        },
      };
    case UPDATE_WARNING_REPEAT:
      return {
        ...state,
        config: {
          ...state.config,
          alerts: {
            ...state.config.alerts,
            thresholds: {
              ...state.config.alerts.thresholds,
              [action.payload.alertID]: {
                ...state.config.alerts.thresholds[action.payload.alertID],
                warning: {
                  ...state.config.alerts.thresholds[action.payload.alertID].warning,
                  repeat: action.payload.repeat,
                },
              },
            },
          },
        },
      };
    case UPDATE_WARNING_THRESHOLD:
      return {
        ...state,
        config: {
          ...state.config,
          alerts: {
            ...state.config.alerts,
            thresholds: {
              ...state.config.alerts.thresholds,
              [action.payload.alertID]: {
                ...state.config.alerts.thresholds[action.payload.alertID],
                warning: {
                  ...state.config.alerts.thresholds[action.payload.alertID].warning,
                  threshold: action.payload.threshold,
                },
              },
            },
          },
        },
      };
    case UPDATE_WARNING_TIMEWINDOW:
      return {
        ...state,
        config: {
          ...state.config,
          alerts: {
            ...state.config.alerts,
            thresholds: {
              ...state.config.alerts.thresholds,
              [action.payload.alertID]: {
                ...state.config.alerts.thresholds[action.payload.alertID],
                warning: {
                  ...state.config.alerts.thresholds[action.payload.alertID].warning,
                  timewindow: action.payload.timewindow,
                },
              },
            },
          },
        },
      };
    case UPDATE_WARNING_ENABLED:
      return {
        ...state,
        config: {
          ...state.config,
          alerts: {
            ...state.config.alerts,
            thresholds: {
              ...state.config.alerts.thresholds,
              [action.payload.alertID]: {
                ...state.config.alerts.thresholds[action.payload.alertID],
                warning: {
                  ...state.config.alerts.thresholds[action.payload.alertID].warning,
                  enabled: action.payload.enabled,
                },
              },
            },
          },
        },
      };
    case UPDATE_CRITICAL_DELAY:
      return {
        ...state,
        config: {
          ...state.config,
          alerts: {
            ...state.config.alerts,
            thresholds: {
              ...state.config.alerts.thresholds,
              [action.payload.alertID]: {
                ...state.config.alerts.thresholds[action.payload.alertID],
                critical: {
                  ...state.config.alerts.thresholds[action.payload.alertID].critical,
                  delay: action.payload.delay,
                },
              },
            },
          },
        },
      };
    case UPDATE_CRITICAL_REPEAT:
      return {
        ...state,
        config: {
          ...state.config,
          alerts: {
            ...state.config.alerts,
            thresholds: {
              ...state.config.alerts.thresholds,
              [action.payload.alertID]: {
                ...state.config.alerts.thresholds[action.payload.alertID],
                critical: {
                  ...state.config.alerts.thresholds[action.payload.alertID].critical,
                  repeat: action.payload.repeat,
                },
              },
            },
          },
        },
      };
    case UPDATE_CRITICAL_THRESHOLD:
      return {
        ...state,
        config: {
          ...state.config,
          alerts: {
            ...state.config.alerts,
            thresholds: {
              ...state.config.alerts.thresholds,
              [action.payload.alertID]: {
                ...state.config.alerts.thresholds[action.payload.alertID],
                critical: {
                  ...state.config.alerts.thresholds[action.payload.alertID].critical,
                  threshold: action.payload.threshold,
                },
              },
            },
          },
        },
      };
    case UPDATE_CRITICAL_TIMEWINDOW:
      return {
        ...state,
        config: {
          ...state.config,
          alerts: {
            ...state.config.alerts,
            thresholds: {
              ...state.config.alerts.thresholds,
              [action.payload.alertID]: {
                ...state.config.alerts.thresholds[action.payload.alertID],
                critical: {
                  ...state.config.alerts.thresholds[action.payload.alertID].critical,
                  timewindow: action.payload.timewindow,
                },
              },
            },
          },
        },
      };
    case UPDATE_CRITICAL_ENABLED:
      return {
        ...state,
        config: {
          ...state.config,
          alerts: {
            ...state.config.alerts,
            thresholds: {
              ...state.config.alerts.thresholds,
              [action.payload.alertID]: {
                ...state.config.alerts.thresholds[action.payload.alertID],
                critical: {
                  ...state.config.alerts.thresholds[action.payload.alertID].critical,
                  enabled: action.payload.enabled,
                },
              },
            },
          },
        },
      };
    case UPDATE_ALERT_ENABLED:
      return {
        ...state,
        config: {
          ...state.config,
          alerts: {
            ...state.config.alerts,
            thresholds: {
              ...state.config.alerts.thresholds,
              [action.payload.alertID]: {
                ...state.config.alerts.thresholds[action.payload.alertID],
                enabled: action.payload.enabled,
              },
            },
          },
        },
      };
    case UPDATE_ALERT_SEVERTY_LEVEL:
      return {
        ...state,
        config: {
          ...state.config,
          alerts: {
            ...state.config.alerts,
            severties: {
              ...state.config.alerts.severties,
              [action.payload.alertID]: {
                ...state.config.alerts.severties[action.payload.alertID],
                severtiy: action.payload.severtiy,
              },
            },
          },
        },
      };
    case UPDATE_ALERT_SEVERTY_ENABLED:
      return {
        ...state,
        config: {
          ...state.config,
          alerts: {
            ...state.config.alerts,
            severties: {
              ...state.config.alerts.severties,
              [action.payload.alertID]: {
                ...state.config.alerts.severties[action.payload.alertID],
                enabled: action.payload.enabled,
              },
            },
          },
        },
      };
    default:
      return state;
  }
}

export default chainsReducer;
