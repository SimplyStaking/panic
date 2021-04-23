import { combineReducers } from 'redux';
import ChangePageReducer from './pageChange';
import ChangeStepReducer from './stepChange';
import {
  TelegramsReducer,
  TwiliosReducer,
  EmailsReducer,
  PagerDutyReducer,
  OpsGenieReducer,
  SlacksReducer,
} from './channelsReducer';
import {
  SubstrateNodesReducer,
  SubstrateChainsReducer,
  CurrentSubstrateChain,
} from './substrateChainsReducer';
import {
  CosmosNodesReducer,
  CosmosChainsReducer,
  CurrentCosmosChain,
// eslint-disable-next-line import/named
} from './cosmosChainsReducer';
import {
  RepositoryReducer,
  DockerReducer,
  SystemsReducer,
  PeriodicReducer,
  KmsReducer,
  GeneralReducer,
} from './generalReducer';
import UsersReducer from './usersReducer';
import LoginReducer from './loginReducer';

export default combineReducers({
  ChangePageReducer,
  ChangeStepReducer,
  TelegramsReducer,
  SlacksReducer,
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
  DockerReducer,
  SystemsReducer,
  PeriodicReducer,
  GeneralReducer,
  KmsReducer,
  UsersReducer,
  LoginReducer,
});
