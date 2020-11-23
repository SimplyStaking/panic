import React from 'react';
import { Box } from '@material-ui/core';
import classNames from "classnames";
import { makeStyles } from "@material-ui/core/styles";
import Title from '../global/title';
import GridContainer from "components/material_ui/Grid/GridContainer.js";
import GridItem from "components/material_ui/Grid/GridItem.js";
import MainText from '../global/mainText';
import LoginContainer from '../../containers/welcome/loginContainer';
import NavigationButtonContainer from
  '../../containers/global/navigationButtonContainer';
import { CHANNELS_PAGE, START } from '../../constants/constants';
import Data from '../../data/welcome';
import styles from "assets/jss/material-kit-react/views/components.js";
import Footer from 'components/material_ui/Footer/Footer.js';

const useStyles = makeStyles(styles);

function WelcomePage() {
  const classes = useStyles();
  return (
      <div className={classes.backgroundImage}>
      <div className={classes.container}>
        <GridContainer>
          <GridItem>
            <div className={classes.brand}>
              <h1 className={classes.title}>
                PANIC Monitoring and Alerting for Blockchains
              </h1>
            </div>
          </GridItem>
        </GridContainer>
      </div>
      <br></br>
      <br></br>
      <div>
        <LoginContainer />        
      </div>
      <NavigationButtonContainer
        text={START}
        navigation={CHANNELS_PAGE}
      />
    </div>
  );
}

export default WelcomePage;
