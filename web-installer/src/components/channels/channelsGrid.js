import React from 'react';
import { makeStyles } from '@material-ui/core/styles';
import { Grid, Box } from '@material-ui/core';
import ChannelsContainer from '../../containers/channels/channelsContainer';

const useStyles = makeStyles((theme) => ({
  root: {
    flexGrow: 1,
  },
  paper: {
    padding: theme.spacing(2),
    textAlign: 'center',
    color: theme.palette.text.primary,
  },
  icon: {
    paddingRight: '1rem',
  },
  heading: {
    fontSize: theme.typography.pxToRem(15),
    fontWeight: theme.typography.fontWeightRegular,
  },
}));

function ChannelsGrid() {
  const classes = useStyles();

  return (
    <Box p={2} className={classes.root}>
      <Box
        p={3}
        border={1}
        borderRadius="borderRadius"
        borderColor="grey.300"
      >
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <ChannelsContainer />
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
}

export default ChannelsGrid;
