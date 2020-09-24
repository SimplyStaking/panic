import { combineReducers } from 'redux';
import ChangePageReducer from './pageChange';
import ChangeStepReducer from './stepChange';
import {
  TelegramsReducer, TwiliosReducer, EmailsReducer, PagerDutyReducer,
  OpsGenieReducer,
} from './channelsReducer';
// import CosmosChainsReducer from './cosmosChainsReducer';
import SubstrateChainsReducer from './substrateChainsReducer';
import { RepositoryReducer, SystemsReducer, periodicReducer } from './generalReducer';
import { CosmosNodesReducer, CosmosChainsReducer, CurrentCosmosChain } from './cosmosChainsReducer';
import UsersReducer from './usersReducer';
import LoginReducer from './loginReducer';

export default combineReducers({
  ChangePageReducer,
  ChangeStepReducer,
  TelegramsReducer,
  TwiliosReducer,
  EmailsReducer,
  PagerDutyReducer,
  OpsGenieReducer,
  CosmosNodesReducer,
  CosmosChainsReducer,
  CurrentCosmosChain,
  SubstrateChainsReducer,
  RepositoryReducer,
  SystemsReducer,
  periodicReducer,
  UsersReducer,
  LoginReducer,
});
