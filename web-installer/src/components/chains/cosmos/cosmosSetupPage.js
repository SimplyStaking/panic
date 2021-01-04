import React from 'react';
import { makeStyles } from '@material-ui/core/styles';
import StepManager from 'containers/chains/cosmos/stepManager';
import Data from 'data/cosmos';
import Parallax from 'components/material_ui/Parallax/Parallax.js';
import GridItem from 'components/material_ui/Grid/GridItem.js';
import GridContainer from 'components/material_ui/Grid/GridContainer.js';
import styles from 'assets/jss/material-kit-react/views/componentsSections/channelsStyle.js';
import Card from 'components/material_ui/Card/Card.js';
import CardBody from 'components/material_ui/Card/CardBody.js';
import Background from 'assets/img/backgrounds/background.png';

const useStyles = makeStyles(styles);

/*
 * Main cosmos setup page, this will be constant through out the cosmos chain
 * setup process. What will change is whatever the StepManager returns. This
 * depends on what is currently set in the state through redux. E.g if the step
 * is set as the NODES_STEP in redux then the nodes form and table will be
 * rendered.
 */
function CosmosSetupPage() {
  const classes = useStyles();

  return (
    <div>
      <Parallax image={Background}>
        <div className={classes.container}>
          <GridContainer>
            <GridItem>
              <div className={classes.brand}>
                <h1 className={classes.title}>{Data.cosmos.title}</h1>
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

export default CosmosSetupPage;
