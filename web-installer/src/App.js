import React from 'react';

import { makeStyles } from '@material-ui/core/styles';

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
    </div>
  );
}

export default App;
