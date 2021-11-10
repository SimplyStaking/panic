import { createStore } from 'redux';
import { persistStore, persistReducer } from 'redux-persist';
import storage from 'redux-persist/lib/storage';
import rootReducer from '../reducers';

const persistConfig = {
  key: 'root',
  storage,
};

export const store = createStore(persistReducer(persistConfig, rootReducer));
export const persistor = persistStore(store);
