import React from 'react';
import { makeStyles } from '@material-ui/core/styles';
import {
  ToastsContainer, ToastsContainerPosition, ToastsStore,
} from 'react-toasts';
import SideBar from './components/global/sidebar';
import PageManger from './containers/global/pageManager';

import './App.css';

const useStyles = makeStyles(() => ({
  root: {
    display: 'flex',
  },
}));

function App() {
  const classes = useStyles();

  return (
    <div className={classes.root}>
      <SideBar />
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
