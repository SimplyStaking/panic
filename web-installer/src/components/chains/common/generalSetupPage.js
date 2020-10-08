import React from 'react';
import { makeStyles } from '@material-ui/core/styles';
import { Grid, Box } from '@material-ui/core';
import Title from '../../global/title';
import MainText from '../../global/mainText';
import StepManager from '../../../containers/chains/common/stepManager';
import Data from '../../../data/general';

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

/*
 * Main general setup page, this will be constant through out the general
 * setup process. What will change is whatever the StepManager returns. This
 * depends on what is currently set in the state through redux. E.g if the step
 * is set as the REPOS_STEP in redux then the repositories form and table will
 * be rendered.
*/
function GeneralSetupPage() {
  const classes = useStyles();

  return (
    <div>
      <Title
        text={Data.general.title}
      />
      <MainText
        text={Data.general.description}
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
              <StepManager />
            </Grid>
          </Grid>
        </Box>
      </Box>
    </div>
  );
}

export default GeneralSetupPage;
