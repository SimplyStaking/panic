/*
  Reference to understand this reducer code
  https://redux.js.org/recipes/structuring-reducers/refactoring-reducer-example
*/

import {
  ADD_CHAIN_SUBSTRATE, ADD_NODE_SUBSTRATE, ADD_REPOSITORY_SUBSTRATE, REMOVE_NODE_SUBSTRATE,
  REMOVE_REPOSITORY_SUBSTRATE, ADD_KMS_SUBSTRATE, REMOVE_KMS_SUBSTRATE, SET_ALERTS_SUBSTRATE,
  ADD_CONFIG_SUBSTRATE, REMOVE_CONFIG_SUBSTRATE, RESET_CONFIG_SUBSTRATE,
  LOAD_CONFIG_SUBSTRATE, ADD_TELEGRAM_CHANNEL_SUBSTRATE,
  REMOVE_TELEGRAM_CHANNEL_SUBSTRATE, ADD_TWILIO_CHANNEL_SUBSTRATE,
  REMOVE_TWILIO_CHANNEL_SUBSTRATE, ADD_EMAIL_CHANNEL_SUBSTRATE,
  REMOVE_EMAIL_CHANNEL_SUBSTRATE, ADD_PAGERDUTY_CHANNEL_SUBSTRATE,
  REMOVE_PAGERDUTY_CHANNEL_SUBSTRATE, ADD_OPSGENIE_CHANNEL_SUBSTRATE,
  REMOVE_OPSGENIE_CHANNEL_SUBSTRATE, UPDATE_WARNING_DELAY_SUBSTRATE,
  UPDATE_WARNING_REPEAT_SUBSTRATE, UPDATE_WARNING_THRESHOLD_SUBSTRATE,
  UPDATE_WARNING_TIMEWINDOW_SUBSTRATE, UPDATE_WARNING_ENABLED_SUBSTRATE,
  UPDATE_CRITICAL_DELAY_SUBSTRATE, UPDATE_CRITICAL_REPEAT_SUBSTRATE,
  UPDATE_CRITICAL_THRESHOLD_SUBSTRATE, UPDATE_CRITICAL_TIMEWINDOW_SUBSTRATE,
  UPDATE_CRITICAL_ENABLED_SUBSTRATE, UPDATE_ALERT_ENABLED_SUBSTRATE,
  UPDATE_ALERT_SEVERTY_LEVEL_SUBSTRATE, UPDATE_ALERT_SEVERTY_ENABLED_SUBSTRATE,
} from '../actions/types';

import { INFO, WARNING, CRITICAL } from '../../constants/constants';

const initialstate = {
  substrateConfigs: [],
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
        alert6: {
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
          severity: CRITICAL,
          enabled: true,
        },
        alert2: {
          name: 'Node inaccessible on startup',
          severity: WARNING,
          enabled: true,
        },
        alert3: {
          name: 'Slashed',
          severity: CRITICAL,
          enabled: true,
        },
        alert4: {
          name: 'Node is syncing',
          severity: WARNING,
          enabled: true,
        },
        alert5: {
          name: 'Validator is not active in this session',
          severity: WARNING,
          enabled: true,
        },
        alert6: {
          name: 'Validator set size increased',
          severity: INFO,
          enabled: true,
        },
        alert7: {
          name: 'Validator set size decreased',
          severity: INFO,
          enabled: true,
        },
        alert8: {
          name: 'Validator was declared as offline by the blockchain',
          severity: WARNING,
          enabled: true,
        },
        alert9: {
          name: 'Validator did not author a block and sent no heartbeats in the previous session',
          severity: WARNING,
          enabled: false,
        },
        alert10: {
          name: 'A new payout is pending',
          severity: WARNING,
          enabled: false,
        },
        alert11: {
          name: 'New proposal submitted',
          severity: INFO,
          enabled: false,
        },
        alert12: {
          name: 'Proposal conducted',
          severity: INFO,
          enabled: false,
        },
        alert13: {
          name: 'Delegated balance increase',
          severity: INFO,
          enabled: false,
        },
        alert14: {
          name: 'Delegated balance decrease',
          severity: INFO,
          enabled: false,
        },
        alert15: {
          name: 'Bonded balance increased',
          severity: INFO,
          enabled: false,
        },
        alert16: {
          name: 'Bonded balance decreased',
          severity: INFO,
          enabled: false,
        },
        alert17: {
          name: 'Free balance increased',
          severity: INFO,
          enabled: false,
        },
        alert18: {
          name: 'Free balance decreased',
          severity: INFO,
          enabled: false,
        },
        alert19: {
          name: 'Reserved balance increased',
          severity: INFO,
          enabled: false,
        },
        alert20: {
          name: 'Reserved balance decreased',
          severity: INFO,
          enabled: false,
        },
        alert21: {
          name: 'Nominated balance increased',
          severity: INFO,
          enabled: false,
        },
        alert22: {
          name: 'Nominated balance decreased',
          severity: INFO,
          enabled: false,
        },
        alert23: {
          name: 'Validator is not elected for next session',
          severity: WARNING,
          enabled: true,
        },
        alert24: {
          name: 'Validator has been disabled in session',
          severity: CRITICAL,
          enabled: true,
        },
        alert25: {
          name: 'New Council proposal',
          severity: INFO,
          enabled: true,
        },
        alert26: {
          name: 'Validator is now part of the council',
          severity: INFO,
          enabled: true,
        },
        alert27: {
          name: 'Validator is no longer part of the council',
          severity: INFO,
          enabled: true,
        },
        alert28: {
          name: 'A new treasury proposal has been submitted',
          severity: INFO,
          enabled: true,
        },
        alert29: {
          name: 'A new tip proposal has been submitted',
          severity: INFO,
          enabled: true,
        },
        alert30: {
          name: 'New Referendum submitted',
          severity: INFO,
          enabled: true,
        },
        alert31: {
          name: 'Referendum completed',
          severity: INFO,
          enabled: true,
        },
      },
    },
  },
};

function substrateChainsReducer(state = initialstate, action) {
  switch (action.type) {
    case ADD_CHAIN_SUBSTRATE:
      return {
        ...state,
        config: {
          ...state.config,
          chainName: action.payload.chainName,
        },
      };
    case ADD_NODE_SUBSTRATE:
      return {
        ...state,
        config: {
          ...state.config,
          nodes: state.config.nodes.concat(action.payload),
        },
      };
    case REMOVE_NODE_SUBSTRATE:
      return {
        ...state,
        config: {
          ...state.config,
          nodes: state.config.nodes.filter((node) => node !== action.payload),
        },
      };
    case ADD_REPOSITORY_SUBSTRATE:
      return {
        ...state,
        config: {
          ...state.config,
          repositories: state.config.repositories.concat(action.payload),
        },
      };
    case REMOVE_REPOSITORY_SUBSTRATE:
      return {
        ...state,
        config: {
          ...state.config,
          repositories: state.config.repositories.filter(
            (repository) => repository !== action.payload,
          ),
        },
      };
    case ADD_KMS_SUBSTRATE:
      return {
        ...state,
        config: {
          ...state.config,
          kmses: state.config.kmses.concat(action.payload),
        },
      };
    case REMOVE_KMS_SUBSTRATE:
      return {
        ...state,
        config: {
          ...state.config,
          kmses: state.config.kmses.filter(
            (kms) => kms !== action.payload,
          ),
        },
      };
    case ADD_TELEGRAM_CHANNEL_SUBSTRATE:
      return {
        ...state,
        config: {
          ...state.config,
          telegrams: state.config.telegrams.concat(action.payload),
        },
      };
    case REMOVE_TELEGRAM_CHANNEL_SUBSTRATE:
      return {
        ...state,
        config: {
          ...state.config,
          telegrams: state.config.telegrams.filter(
            (telegram) => telegram !== action.payload,
          ),
        },
      };
    case ADD_OPSGENIE_CHANNEL_SUBSTRATE:
      return {
        ...state,
        config: {
          ...state.config,
          opsgenies: state.config.opsgenies.concat(action.payload),
        },
      };
    case REMOVE_OPSGENIE_CHANNEL_SUBSTRATE:
      return {
        ...state,
        config: {
          ...state.config,
          opsgenies: state.config.opsgenies.filter(
            (opsgenie) => opsgenie !== action.payload,
          ),
        },
      };
    case ADD_EMAIL_CHANNEL_SUBSTRATE:
      return {
        ...state,
        config: {
          ...state.config,
          emails: state.config.emails.concat(action.payload),
        },
      };
    case REMOVE_EMAIL_CHANNEL_SUBSTRATE:
      return {
        ...state,
        config: {
          ...state.config,
          emails: state.config.emails.filter(
            (email) => email !== action.payload,
          ),
        },
      };
    case ADD_TWILIO_CHANNEL_SUBSTRATE:
      return {
        ...state,
        config: {
          ...state.config,
          twilios: state.config.twilios.concat(action.payload),
        },
      };
    case REMOVE_TWILIO_CHANNEL_SUBSTRATE:
      return {
        ...state,
        config: {
          ...state.config,
          twilios: state.config.twilios.filter(
            (twilio) => twilio !== action.payload,
          ),
        },
      };
    case ADD_PAGERDUTY_CHANNEL_SUBSTRATE:
      return {
        ...state,
        config: {
          ...state.config,
          pagerduties: state.config.pagerduties.concat(action.payload),
        },
      };
    case REMOVE_PAGERDUTY_CHANNEL_SUBSTRATE:
      return {
        ...state,
        config: {
          ...state.config,
          pagerduties: state.config.pagerduties.filter(
            (pagerduty) => pagerduty !== action.payload,
          ),
        },
      };
    case SET_ALERTS_SUBSTRATE:
      return {
        ...state,
        config: {
          ...state.config,
          alerts: action.payload.alerts,
        },
      };
    case ADD_CONFIG_SUBSTRATE:
      return {
        ...state,
        substrateConfigs: state.substrateConfigs.concat(state.config),
      };
    case REMOVE_CONFIG_SUBSTRATE:
      return {
        ...state,
        substrateConfigs: state.substrateConfigs.filter(
          (substrateConfig) => substrateConfig !== action.payload,
        ),
      };
    case RESET_CONFIG_SUBSTRATE:
      return {
        ...state,
        config: initialstate.config,
      };
    case LOAD_CONFIG_SUBSTRATE:
      return {
        ...state,
        config: state.substrateConfigs.filter(
          (substrateConfig) => substrateConfig === action.payload,
        )[0],
      };
    case UPDATE_WARNING_DELAY_SUBSTRATE:
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
    case UPDATE_WARNING_REPEAT_SUBSTRATE:
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
    case UPDATE_WARNING_THRESHOLD_SUBSTRATE:
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
    case UPDATE_WARNING_TIMEWINDOW_SUBSTRATE:
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
    case UPDATE_WARNING_ENABLED_SUBSTRATE:
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
    case UPDATE_CRITICAL_DELAY_SUBSTRATE:
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
    case UPDATE_CRITICAL_REPEAT_SUBSTRATE:
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
    case UPDATE_CRITICAL_THRESHOLD_SUBSTRATE:
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
    case UPDATE_CRITICAL_TIMEWINDOW_SUBSTRATE:
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
    case UPDATE_CRITICAL_ENABLED_SUBSTRATE:
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
    case UPDATE_ALERT_ENABLED_SUBSTRATE:
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
    case UPDATE_ALERT_SEVERTY_LEVEL_SUBSTRATE:
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
                severity: action.payload.severity,
              },
            },
          },
        },
      };
    case UPDATE_ALERT_SEVERTY_ENABLED_SUBSTRATE:
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

export default substrateChainsReducer;
