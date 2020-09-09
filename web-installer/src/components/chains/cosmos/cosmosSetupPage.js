import React from 'react';
import { makeStyles } from '@material-ui/core/styles';
import { Grid, Box } from '@material-ui/core';
import Title from '../../global/title';
import MainText from '../../global/mainText';
import NavigationButtonContainer from '../../../containers/global/navigationButtonContainer';
import {
  CHANNELS_PAGE, OTHER_PAGE, DONE, BACK,
} from '../../../constants/constants';
import Data from '../../../data/cosmos';

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

function CosmosSetupPage() {
  const classes = useStyles();

  return (
    <div>
      <Title
        text={Data.cosmos.title}
      />
      <MainText
        text={Data.cosmos.description}
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
              <h1>Chicken Shit</h1>
            </Grid>
          </Grid>
        </Box>
      </Box>
      <NavigationButtonContainer
        text={DONE}
        navigation={OTHER_PAGE}
      />
      <NavigationButtonContainer
        text={BACK}
        navigation={CHANNELS_PAGE}
      />
    </div>
  );
}

export default CosmosSetupPage;
