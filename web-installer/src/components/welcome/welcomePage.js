import React from 'react';
import { Box } from '@material-ui/core';
import Title from '../global/title';
import MainText from '../global/mainText';
import LoginContainer from '../../containers/welcome/loginContainer';
import NavigationButtonContainer from
  '../../containers/global/navigationButtonContainer';
import { CHANNELS_PAGE, START } from '../../constants/constants';
import Data from '../../data/welcome';

function WelcomePage() {
  return (
    <div>
      <Title
        text={Data.welcome.title}
      />
      <MainText
        text={Data.welcome.description}
      />
      <Box p={2} className="flex_root">
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
