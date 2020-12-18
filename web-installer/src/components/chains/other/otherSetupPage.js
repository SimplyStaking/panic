import React from 'react';
import { makeStyles } from "@material-ui/core/styles";
import StepManager from 'containers/chains/other/stepManager';
import Data from 'data/general';
import Parallax from "components/material_ui/Parallax/Parallax.js";
import GridItem from "components/material_ui/Grid/GridItem.js";
import GridContainer from "components/material_ui/Grid/GridContainer.js";
import styles from "assets/jss/material-kit-react/views/componentsSections/channelsStyle.js";
import Card from "components/material_ui/Card/Card.js";
import CardBody from "components/material_ui/Card/CardBody.js";

const useStyles = makeStyles(styles);

/*
 * Main general setup page, this will be constant through out the general
 * setup process. What will change is whatever the StepManager returns. This
 * depends on what is currently set in the state through redux. E.g if the step
 * is set as the REPOS_STEP in redux then the repositories form and table will
 * be rendered.
*/
function OtherSetupPage() {
  const classes = useStyles();

  return (
    <div>
      <Parallax image={require("assets/img/backgrounds/background.png")}>
        <div className={classes.container}>
          <GridContainer>
            <GridItem>
              <div className={classes.brand}>
                <h1 className={classes.title}>
                  {Data.general.title}
                </h1>
              </div>
            </GridItem>
          </GridContainer>
        </div>
      </Parallax>
      <div className={classes.mainRaised}>
        <Card>
          <CardBody>
            <div className={classes.container}>
              <StepManager />
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

export default OtherSetupPage;
