import { combineReducers } from 'redux';
import ChangePageReducer from './pageChange';
import ChannelsReducer from './channelsReducer';
import ChainsReducer from './chainsReducer';

export default combineReducers({
  ChangePageReducer,
  ChannelsReducer,
  ChainsReducer,
});
