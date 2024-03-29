import _ from 'lodash';
import { combineReducers } from 'redux';
import {
  ADD_TELEGRAM,
  REMOVE_TELEGRAM,
  ADD_TWILIO,
  REMOVE_TWILIO,
  ADD_EMAIL,
  REMOVE_EMAIL,
  ADD_PAGERDUTY,
  REMOVE_PAGERDUTY,
  ADD_OPSGENIE,
  REMOVE_OPSGENIE,
  ADD_TELEGRAM_CHANNEL,
  REMOVE_TELEGRAM_CHANNEL,
  ADD_TWILIO_CHANNEL,
  REMOVE_TWILIO_CHANNEL,
  ADD_EMAIL_CHANNEL,
  REMOVE_EMAIL_CHANNEL,
  ADD_PAGERDUTY_CHANNEL,
  REMOVE_PAGERDUTY_CHANNEL,
  ADD_OPSGENIE_CHANNEL,
  REMOVE_OPSGENIE_CHANNEL,
  ADD_SLACK,
  REMOVE_SLACK,
  ADD_SLACK_CHANNEL,
  REMOVE_SLACK_CHANNEL,
} from 'redux/actions/types';

// Reducers to add and remove slack configurations from global state
function slacksById(state = {}, action) {
  let parsed = {};
  switch (action.type) {
    case ADD_SLACK:
      return {
        ...state,
        [action.payload.id]: action.payload,
      };
    case REMOVE_SLACK:
      return _.omit(state, action.payload.id);
    case ADD_SLACK_CHANNEL:
      parsed = JSON.parse(JSON.stringify(action.payload));
      return {
        ...state,
        [action.payload.id]: parsed,
      };
    case REMOVE_SLACK_CHANNEL:
      parsed = JSON.parse(JSON.stringify(action.payload));
      return {
        ...state,
        [action.payload.id]: parsed,
      };
    default:
      return state;
  }
}

// Reducers to remove from list of all telegrams
function allSlacks(state = [], action) {
  switch (action.type) {
    case ADD_SLACK:
      if (state.includes(action.payload.id)) {
        return state;
      }
      return state.concat(action.payload.id);
    case REMOVE_SLACK:
      return state.filter((config) => config !== action.payload.id);
    default:
      return state;
  }
}

const SlacksReducer = combineReducers({
  byId: slacksById,
  allIds: allSlacks,
});

// Reducers to add and remove telegram configurations from global state
function telegramsById(state = {}, action) {
  let parsed = {};
  switch (action.type) {
    case ADD_TELEGRAM:
      return {
        ...state,
        [action.payload.id]: action.payload,
      };
    case REMOVE_TELEGRAM:
      return _.omit(state, action.payload.id);
    case ADD_TELEGRAM_CHANNEL:
      parsed = JSON.parse(JSON.stringify(action.payload));
      return {
        ...state,
        [action.payload.id]: parsed,
      };
    case REMOVE_TELEGRAM_CHANNEL:
      parsed = JSON.parse(JSON.stringify(action.payload));
      return {
        ...state,
        [action.payload.id]: parsed,
      };
    default:
      return state;
  }
}

// Reducers to remove from list of all telegrams
function allTelegrams(state = [], action) {
  switch (action.type) {
    case ADD_TELEGRAM:
      if (state.includes(action.payload.id)) {
        return state;
      }
      return state.concat(action.payload.id);
    case REMOVE_TELEGRAM:
      return state.filter((config) => config !== action.payload.id);
    default:
      return state;
  }
}

const TelegramsReducer = combineReducers({
  byId: telegramsById,
  allIds: allTelegrams,
});

// Reducers to add and remove twilio configurations from global state
function twiliosById(state = {}, action) {
  let parsed = {};
  switch (action.type) {
    case ADD_TWILIO:
      return {
        ...state,
        [action.payload.id]: action.payload,
      };
    case REMOVE_TWILIO:
      return _.omit(state, action.payload.id);
    case ADD_TWILIO_CHANNEL:
      parsed = JSON.parse(JSON.stringify(action.payload));
      return {
        ...state,
        [action.payload.id]: parsed,
      };
    case REMOVE_TWILIO_CHANNEL:
      parsed = JSON.parse(JSON.stringify(action.payload));
      return {
        ...state,
        [action.payload.id]: parsed,
      };
    default:
      return state;
  }
}

// Reducers to remove from list of all twilios
function allTwilios(state = [], action) {
  switch (action.type) {
    case ADD_TWILIO:
      if (state.includes(action.payload.id)) {
        return state;
      }
      return state.concat(action.payload.id);
    case REMOVE_TWILIO:
      return state.filter((config) => config !== action.payload.id);
    default:
      return state;
  }
}

const TwiliosReducer = combineReducers({
  byId: twiliosById,
  allIds: allTwilios,
});

// Reducers to add and remove email configurations from global state
function emailsById(state = {}, action) {
  let parsed = {};
  switch (action.type) {
    case ADD_EMAIL:
      return {
        ...state,
        [action.payload.id]: action.payload,
      };
    case REMOVE_EMAIL:
      return _.omit(state, action.payload.id);
    case ADD_EMAIL_CHANNEL:
      parsed = JSON.parse(JSON.stringify(action.payload));
      return {
        ...state,
        [action.payload.id]: parsed,
      };
    case REMOVE_EMAIL_CHANNEL:
      parsed = JSON.parse(JSON.stringify(action.payload));
      return {
        ...state,
        [action.payload.id]: parsed,
      };
    default:
      return state;
  }
}

// Reducers to remove from list of all emails
function allEmails(state = [], action) {
  switch (action.type) {
    case ADD_EMAIL:
      if (state.includes(action.payload.id)) {
        return state;
      }
      return state.concat(action.payload.id);
    case REMOVE_EMAIL:
      return state.filter((config) => config !== action.payload.id);
    default:
      return state;
  }
}

const EmailsReducer = combineReducers({
  byId: emailsById,
  allIds: allEmails,
});

// Reducers to add and remove pagerduty configurations from global state
function pagerdutyById(state = {}, action) {
  let parsed = {};
  switch (action.type) {
    case ADD_PAGERDUTY:
      return {
        ...state,
        [action.payload.id]: action.payload,
      };
    case REMOVE_PAGERDUTY:
      return _.omit(state, action.payload.id);
    case ADD_PAGERDUTY_CHANNEL:
      parsed = JSON.parse(JSON.stringify(action.payload));
      return {
        ...state,
        [action.payload.id]: parsed,
      };
    case REMOVE_PAGERDUTY_CHANNEL:
      parsed = JSON.parse(JSON.stringify(action.payload));
      return {
        ...state,
        [action.payload.id]: parsed,
      };
    default:
      return state;
  }
}

// Reducers to remove from list of all pagerduties
function allPagerDuties(state = [], action) {
  switch (action.type) {
    case ADD_PAGERDUTY:
      if (state.includes(action.payload.id)) {
        return state;
      }
      return state.concat(action.payload.id);
    case REMOVE_PAGERDUTY:
      return state.filter((config) => config !== action.payload.id);
    default:
      return state;
  }
}

const PagerDutyReducer = combineReducers({
  byId: pagerdutyById,
  allIds: allPagerDuties,
});

// Reducers to add and remove pagerduty configurations from global state
function opsgenieById(state = {}, action) {
  let parsed = {};
  switch (action.type) {
    case ADD_OPSGENIE:
      return {
        ...state,
        [action.payload.id]: action.payload,
      };
    case REMOVE_OPSGENIE:
      return _.omit(state, action.payload.id);
    case ADD_OPSGENIE_CHANNEL:
      parsed = JSON.parse(JSON.stringify(action.payload));
      return {
        ...state,
        [action.payload.id]: parsed,
      };
    case REMOVE_OPSGENIE_CHANNEL:
      parsed = JSON.parse(JSON.stringify(action.payload));
      return {
        ...state,
        [action.payload.id]: parsed,
      };
    default:
      return state;
  }
}

// Reducers to remove from list of all pagerduties
function allOpsGenies(state = [], action) {
  switch (action.type) {
    case ADD_OPSGENIE:
      if (state.includes(action.payload.id)) {
        return state;
      }
      return state.concat(action.payload.id);
    case REMOVE_OPSGENIE:
      return state.filter((config) => config !== action.payload.id);
    default:
      return state;
  }
}

const OpsGenieReducer = combineReducers({
  byId: opsgenieById,
  allIds: allOpsGenies,
});

export {
  OpsGenieReducer,
  PagerDutyReducer,
  EmailsReducer,
  TwiliosReducer,
  TelegramsReducer,
  SlacksReducer,
};
