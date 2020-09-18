import React from 'react';
import { Box } from '@material-ui/core';
import { makeStyles } from '@material-ui/core/styles';
import Title from '../global/title';
import MainText from '../global/mainText';
import NavigationButtonContainer from '../../containers/global/navigationButtonContainer';
import { CHANNELS_PAGE, START } from '../../constants/constants';
import LoginContainer from '../../containers/welcome/loginContainer';
import Data from '../../data/welcome';

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

function WelcomePage() {
  const classes = useStyles();

  return (
    <div>
      <Title
        text={Data.welcome.title}
      />
      <MainText
        text={Data.welcome.description}
      />
      <Box p={2} className={classes.root}>
        <Box
          p={3}
          border={1}
          borderRadius="borderRadius"
          borderColor="grey.300"
        >
          <LoginContainer />
        </Box>
      </Box>
      <NavigationButtonContainer
        text={START}
        navigation={CHANNELS_PAGE}
      />
    </div>
  );
}

export default WelcomePage;
