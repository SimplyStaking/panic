import React from 'react';

import { makeStyles } from '@material-ui/core/styles';

import SideBar from './components/global/sidebar';
import PageSelector from './containers/pageSelector';

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
      <PageSelector />
    </div>
  );
}

export default App;
