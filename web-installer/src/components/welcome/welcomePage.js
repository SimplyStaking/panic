import React from 'react';
import { Box } from '@material-ui/core';
import { makeStyles } from "@material-ui/core/styles";
import GridContainer from "components/material_ui/Grid/GridContainer.js";
import GridItem from "components/material_ui/Grid/GridItem.js";
import LoginContainer from 'containers/welcome/loginContainer';
import NavigationButtonContainer from 'containers/global/navigationButtonContainer';
import { CHANNELS_PAGE, START } from '../../constants/constants';
import Data from 'data/welcome';
import styles from "assets/jss/material-kit-react/views/components.js";

const useStyles = makeStyles(styles);

function WelcomePage() {
  const classes = useStyles();
  return (
      <div className={classes.backgroundImage}>
        <div className={classes.container}>
          <div className={classes.brand}>
            <GridContainer>
              <GridItem>
                  <h1 className={classes.title}>
                    {Data.title}
                  </h1>
                  <h2 className={classes.subtitle}>
                    {Data.description}
                  </h2>
              </GridItem>
            </GridContainer>
          </div>
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
