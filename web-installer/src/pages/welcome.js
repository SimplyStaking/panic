import React from 'react';

import Title from '../components/global/title';
import MainText from '../components/global/mainText';
import NavigationButtonContainer from '../containers/global/navigationButtonContainer';
import { CHANNELS_PAGE, START } from '../constants/constants';
import Data from '../data/welcome';

function Welcome() {
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

export default Welcome;
