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
} from './cosmosChainsReducer';
import {
  ChainlinkNodesReducer,
  ChainlinkChainsReducer,
  CurrentChainlinkChain,
} from './chainlinkChainsReducer';
import {
  RepositoryReducer,
  DockerHubReducer,
  SystemsReducer,
  PeriodicReducer,
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
  DockerHubReducer,
  SystemsReducer,
  PeriodicReducer,
  GeneralReducer,
  UsersReducer,
  LoginReducer,
  ChainlinkNodesReducer,
  ChainlinkChainsReducer,
  CurrentChainlinkChain,
});
