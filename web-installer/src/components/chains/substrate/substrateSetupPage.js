import React from 'react';
import StepManager from 'containers/chains/substrate/stepManager';
import Data from 'data/substrate';
import Parallax from 'components/material_ui/Parallax/Parallax';
import GridItem from 'components/material_ui/Grid/GridItem';
import GridContainer from 'components/material_ui/Grid/GridContainer';
import useStyles from 'assets/jss/material-kit-react/views/componentsSections/channelsStyle';
import Card from 'components/material_ui/Card/Card';
import CardBody from 'components/material_ui/Card/CardBody';
import Background from 'assets/img/backgrounds/background.png';

function SubstrateSetupPage() {
  const classes = useStyles();

  return (
    <div>
      <Parallax image={Background}>
        <div className={classes.container}>
          <GridContainer>
            <GridItem>
              <div className={classes.brand}>
                <h1 className={classes.title}>{Data.substrate.title}</h1>
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

export default SubstrateSetupPage;
