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
    alerts: '',
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
