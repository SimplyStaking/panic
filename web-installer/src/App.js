import React from 'react';
import { makeStyles } from '@material-ui/core/styles';
import {
  ToastsContainer, ToastsContainerPosition, ToastsStore,
} from 'react-toasts';
import PageManger from './containers/global/pageManager';

import './App.css';

const useStyles = makeStyles(() => ({
  root: {
    display: 'flex',
  },
}));

/*
* Main application, which loads the PageManager and the ToastsContainer
* PageManager changes which page/form is being viewed through redux
* Toasts Container controls the overlayed notifications when interacting
* with the backend.
*/
function App() {
  const classes = useStyles();

  return (
    <div className={classes.root}>
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
