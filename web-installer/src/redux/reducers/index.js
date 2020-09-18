import { combineReducers } from 'redux';
import ChangePageReducer from './pageChange';
import ChangeStepReducer from './stepChange';
import ChannelsReducer from './channelsReducer';
import CosmosChainsReducer from './cosmosChainsReducer';
import SubstrateChainsReducer from './substrateChainsReducer';
import GeneralReducer from './generalReducer';
import UsersReducer from './usersReducer';
import LoginReducer from './loginReducer';

export default combineReducers({
  ChangePageReducer,
  ChangeStepReducer,
  ChannelsReducer,
  CosmosChainsReducer,
  SubstrateChainsReducer,
  GeneralReducer,
  UsersReducer,
  LoginReducer,
});
