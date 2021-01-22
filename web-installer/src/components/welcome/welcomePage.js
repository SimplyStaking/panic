import React from 'react';
import GridContainer from 'components/material_ui/Grid/GridContainer';
import GridItem from 'components/material_ui/Grid/GridItem';
import LoginContainer from 'containers/welcome/loginContainer';
import useStyles from 'assets/jss/material-kit-react/views/components';
import Data from 'data/welcome';

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
      <br />
      <br />
      <div className={classes.topPadded}>
        <LoginContainer />
      </div>
    </div>
  );
}

export default WelcomePage;
