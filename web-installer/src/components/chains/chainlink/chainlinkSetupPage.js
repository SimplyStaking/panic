import React from 'react';
import StepManager from 'containers/chains/chainlink/stepManager';
import Parallax from 'components/material_ui/Parallax/Parallax';
import useStyles from 'assets/jss/material-kit-react/views/componentsSections/channelsStyle';
import Card from 'components/material_ui/Card/Card';
import CardBody from 'components/material_ui/Card/CardBody';
import Background from 'assets/img/backgrounds/ChainlinkHeaderCard.png';

/*
 * Main chainlink setup page, this will be constant through out the chainlink
 * chain setup process. What will change is whatever the StepManager returns.
 * This depends on what is currently set in the state through redux.
 * E.g if the step is set as the NODES_STEP in redux then the nodes form and
 * table will be rendered.
 */
function ChainlinkSetupPage() {
  const classes = useStyles();

  return (
    <div>
      <Parallax image={Background} />
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

export default ChainlinkSetupPage;
