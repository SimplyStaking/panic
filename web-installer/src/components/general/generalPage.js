import React from 'react';
import { Box, Grid } from '@material-ui/core';
import NavigationButtonContainer from 'containers/global/navigationButtonContainer';
import {
  NEXT, USERS_PAGE, CHAINS_PAGE, BACK,
} from 'constants/constants';

import PeriodicFormContainer from 'containers/general/periodicContainer';
import Data from 'data/general';
import GridContainer from 'components/material_ui/Grid/GridContainer';
import Parallax from 'components/material_ui/Parallax/Parallax';
import GridItem from 'components/material_ui/Grid/GridItem';
import useStyles from 'assets/jss/material-kit-react/views/componentsSections/channelsStyle';
import Card from 'components/material_ui/Card/Card';
import CardBody from 'components/material_ui/Card/CardBody';
import Background from 'assets/img/backgrounds/background.png';

function GeneralsPage() {
  const classes = useStyles();

  return (
    <div>
      <Parallax image={Background}>
        <div className={classes.container}>
          <GridContainer>
            <GridItem>
              <div className={classes.brand}>
                <h1 className={classes.title}>{Data.general.title}</h1>
              </div>
            </GridItem>
          </GridContainer>
        </div>
      </Parallax>
      <div className={classes.mainRaised}>
        <Card>
          <CardBody>
            <div className={classes.container}>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <Box p={2} className="flex_root">
                    <Box
                      p={3}
                      borderRadius="borderRadius"
                      borderColor="grey.300"
                    >
                      <PeriodicFormContainer />
                    </Box>
                  </Box>
                </Grid>
                <Grid item xs={12} />
                <Grid item xs={4} />
                <Grid item xs={2}>
                  <NavigationButtonContainer
                    text={BACK}
                    navigation={CHAINS_PAGE}
                  />
                </Grid>
                <Grid item xs={2}>
                  <NavigationButtonContainer
                    text={NEXT}
                    navigation={USERS_PAGE}
                  />
                </Grid>
                <Grid item xs={4} />
                <Grid item xs={12} />
              </Grid>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

export default GeneralsPage;
