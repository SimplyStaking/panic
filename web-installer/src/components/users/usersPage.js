import React from 'react';
import { Grid, Box } from '@material-ui/core';
import { makeStyles } from '@material-ui/core/styles';
import Title from '../global/title';
import MainText from '../global/mainText';
import NavigationButtonContainer from '../../containers/global/navigationButtonContainer';
import { UsersFormContainer, UsersTableContainer } from '../../containers/users/usersContainer';
import {
  WELCOME_PAGE, GENERAL_PAGE, NEXT, BACK,
} from '../../constants/constants';
import Data from '../../data/users';

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

function UsersPage() {
  const classes = useStyles();

  return (
    <div>
      <Title
        text={Data.users.title}
      />
      <MainText
        text={Data.users.description}
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
              <UsersFormContainer />
              <UsersTableContainer />
            </Grid>
          </Grid>
        </Box>
      </Box>
      <NavigationButtonContainer
        text={NEXT}
        navigation={WELCOME_PAGE}
      />
      <NavigationButtonContainer
        text={BACK}
        navigation={GENERAL_PAGE}
      />
    </div>
  );
}

export default UsersPage;
