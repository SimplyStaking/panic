import { combineReducers } from 'redux';
import ChangePageReducer from './pageChange';
import ChangeStepReducer from './stepChange';
import ChannelsReducer from './channelsReducer';
import ChainsReducer from './chainsReducer';

export default combineReducers({
  ChangePageReducer,
  ChangeStepReducer,
  ChannelsReducer,
  ChainsReducer,
});
