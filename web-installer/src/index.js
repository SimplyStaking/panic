import React from 'react';
import ReactDOM from 'react-dom';

import { Provider } from 'react-redux';
import { PersistGate } from 'redux-persist/integration/react';
import { store, persistor } from './redux/store/store';

import './index.css';
import App from './App';

// Uncomment to be able to access the store from Chrome console.
window.store = store;

ReactDOM.render(
  <Provider store={store}>
    <PersistGate loading={null} persistor={persistor}>
      <App />
    </PersistGate>
  </Provider>,
  document.getElementById('root'),
);
