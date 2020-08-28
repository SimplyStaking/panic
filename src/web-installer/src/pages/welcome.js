import React from 'react'

import Title from '../components/global/title';
import MainText from '../components/global/mainText';
import NavigationButtonContainer from '../containers/global/navigationButtonContainer';
import { CHANNELS_PAGE } from "../constants/pages";
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
                text={'Start'}
                navigation={CHANNELS_PAGE}
            />
        </div>
    )
}

export default Welcome;