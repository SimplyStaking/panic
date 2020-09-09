import React from 'react';
import { makeStyles } from '@material-ui/core/styles';
import { Grid, Box } from '@material-ui/core';
import Title from '../global/title';
import MainText from '../global/mainText';
import NavigationButtonContainer from '../../containers/global/navigationButtonContainer';
import ChainAccordion from './chainAccordion';
import CosmosIcon from '../../assets/icons/cosmos.png';
import {
  CHANNELS_PAGE, OTHER_PAGE, DONE, BACK, COSMOS_SETUP_PAGE, NEW,
  COSMOS,
} from '../../constants/constants';
import Data from '../../data/chains';

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

function Chains() {
  const classes = useStyles();

  return (
    <div>
      <Title
        text={Data.chains.title}
      />
      <MainText
        text={Data.chains.description}
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
              <ChainAccordion
                icon={CosmosIcon}
                name={COSMOS}
                button={(
                  <NavigationButtonContainer
                    text={NEW}
                    navigation={COSMOS_SETUP_PAGE}
                  />
                )}
              />
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

export default Chains;
