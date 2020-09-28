import { combineReducers } from 'redux';
import ChangePageReducer from './pageChange';
import ChangeStepReducer from './stepChange';
import {
  TelegramsReducer, TwiliosReducer, EmailsReducer, PagerDutyReducer,
  OpsGenieReducer,
} from './channelsReducer';
import { SubstrateNodesReducer, SubstrateChainsReducer, CurrentSubstrateChain } from './substrateChainsReducer';
import { CosmosNodesReducer, CosmosChainsReducer, CurrentCosmosChain } from './cosmosChainsReducer';
import {
  RepositoryReducer, SystemsReducer, PeriodicReducer, KmsReducer,
} from './generalReducer';
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
  SubstrateNodesReducer,
  SubstrateChainsReducer,
  CurrentSubstrateChain,
  RepositoryReducer,
  SystemsReducer,
  PeriodicReducer,
  KmsReducer,
  UsersReducer,
  LoginReducer,
});
