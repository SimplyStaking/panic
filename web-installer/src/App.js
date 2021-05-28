import React from 'react';
import {
  ToastsContainer, ToastsContainerPosition, ToastsStore,
} from 'react-toasts';
import PageManger from './containers/global/pageManager';
import './App.css';

/*
* Main application, which loads the PageManager and the ToastsContainer
* PageManager changes which page/form is being viewed through redux
* Toasts Container controls the overlay notifications when interacting
* with the backend.
*/
function App() {
  return (
    <div>
      <PageManger />
      <ToastsContainer
        store={ToastsStore}
        position={ToastsContainerPosition.TOP_CENTER}
        lightBackground
      />
    </div>
  );
}

export default App;
