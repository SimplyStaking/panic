import React from 'react';
import { makeStyles } from "@material-ui/core/styles";
import GridContainer from "components/material_ui/Grid/GridContainer.js";
import GridItem from "components/material_ui/Grid/GridItem.js";
import LoginContainer from 'containers/welcome/loginContainer';
import styles from "assets/jss/material-kit-react/views/components.js";
import Data from 'data/welcome';

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
        <div className={classes.topPadded}>
          <LoginContainer />        
        </div>
    </div>
  );
}

export default WelcomePage;
