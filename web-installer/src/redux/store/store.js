import { createStore } from 'redux';
import rootReducer from '../reducers';
// import { loadState, saveState } from './localStorage';

// const persistedState = loadState();

const store = createStore(rootReducer);

// store.subscribe(() => {
//   saveState(store.getState());
// });

export default store;
