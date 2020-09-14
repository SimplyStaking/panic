/*
  Reference to understand this reducer code
  https://redux.js.org/recipes/structuring-reducers/refactoring-reducer-example
*/

import {
  ADD_CHAIN, ADD_NODE, ADD_REPOSITORY, REMOVE_NODE, REMOVE_REPOSITORY,
  ADD_KMS, REMOVE_KMS, SET_ALERTS, ADD_CONFIG, REMOVE_CONFIG,
  ADD_TELEGRAM_CHANNEL, REMOVE_TELEGRAM_CHANNEL,
  ADD_OPSGENIE_CHANNEL, REMOVE_OPSGENIE_CHANNEL, ADD_EMAIL_CHANNEL,
  REMOVE_EMAIL_CHANNEL, ADD_PAGERDUTY_CHANNEL, REMOVE_PAGERDUTY_CHANNEL,
  ADD_TWILIO_CHANNEL, REMOVE_TWILIO_CHANNEL,
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
      thresholds: [
        {
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
        {
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
        {
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
        {
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
        {
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
        {
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
        {
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
        {
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
        {
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
        {
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
        {
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
        {
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
        {
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
      ],
      severties: [
        {
          name: 'Validator inaccessible on startup',
          severtiy: CRITICAL,
          enabled: true,
        },
        {
          name: 'Node inaccessible on startup',
          severtiy: WARNING,
          enabled: true,
        },
        {
          name: 'Slashed',
          severtiy: CRITICAL,
          enabled: true,
        },
        {
          name: 'Slashed',
          severtiy: CRITICAL,
          enabled: true,
        },
        {
          name: 'Node is syncing',
          severtiy: WARNING,
          enabled: true,
        },
        {
          name: 'Validator is not active in this session',
          severtiy: WARNING,
          enabled: true,
        },
        {
          name: 'Validator set size increased',
          severtiy: INFO,
          enabled: true,
        },
        {
          name: 'Validator set size decreased',
          severtiy: INFO,
          enabled: true,
        },
        {
          name: 'Validator is jailed',
          severtiy: CRITICAL,
          enabled: true,
        },
        {
          name: 'Voting power increased',
          severtiy: INFO,
          enabled: false,
        },
        {
          name: 'Validator power decreased',
          severtiy: INFO,
          enabled: false,
        },
        {
          name: 'New proposal submitted',
          severtiy: INFO,
          enabled: false,
        },
        {
          name: 'Proposal conducted',
          severtiy: INFO,
          enabled: false,
        },
        {
          name: 'Delegated balance increase',
          severtiy: INFO,
          enabled: false,
        },
        {
          name: 'Delegagted balance decrease',
          severtiy: INFO,
          enabled: false,
        },
      ],
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
        cosmosConfigs: state.cosmosConfigs.concat(action.payload),
      };
    case REMOVE_CONFIG:
      return {
        ...state,
        cosmosConfigs: state.cosmosConfigs.filter(
          (cosmosConfig) => cosmosConfig !== action.payload,
        ),
      };
    default:
      return state;
  }
}

export default chainsReducer;
