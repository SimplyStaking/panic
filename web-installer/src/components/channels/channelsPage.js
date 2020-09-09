import React from 'react';
import { Grid, Box } from '@material-ui/core';
import { makeStyles } from '@material-ui/core/styles';
import Title from '../global/title';
import MainText from '../global/mainText';
import NavigationButtonContainer from '../../containers/global/navigationButtonContainer';
import ChannelsHolder from './channelsHolder';
import {
  WELCOME_PAGE, CHAINS_PAGE, NEXT, BACK,
} from '../../constants/constants';
import Data from '../../data/channels';

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

function ChannelsPage() {
  const classes = useStyles();

  return (
    <div>
      <Title
        text={Data.channels.title}
      />
      <MainText
        text={Data.channels.description}
      />
      <Box p={2} className={classes.root}>
        <Box
          p={3}
          border={1}
          borderRadius="borderRadius"
          borderColor="grey.300"
        >
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <ChannelsHolder />
            </Grid>
          </Grid>
        </Box>
      </Box>
      <NavigationButtonContainer
        text={NEXT}
        navigation={CHAINS_PAGE}
      />
      <NavigationButtonContainer
        text={BACK}
        navigation={WELCOME_PAGE}
      />
    </div>
  );
}

export default ChannelsPage;
