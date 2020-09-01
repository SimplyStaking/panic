import { combineReducers } from 'redux';
import ChangePageReducer from './pageChange';
import ChannelsReducer from './channelsReducer';

export default combineReducers({ ChangePageReducer, ChannelsReducer });
