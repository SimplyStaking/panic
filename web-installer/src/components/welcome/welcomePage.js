import React from 'react';

import Title from '../global/title';
import MainText from '../global/mainText';
import NavigationButtonContainer from '../../containers/global/navigationButtonContainer';
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
      <NavigationButtonContainer
        text={START}
        navigation={CHANNELS_PAGE}
      />
    </div>
  );
}

export default WelcomePage;
