import React from 'react';
import { makeStyles } from "@material-ui/core/styles";
import { Box } from '@material-ui/core';
import NavigationButtonContainer from 'containers/global/navigationButtonContainer';
import { NEXT, USERS_PAGE, CHAINS_PAGE, BACK } from 'constants/constants';
import { Grid } from '@material-ui/core';
import PeriodicFormContainer from 'containers/general/periodicContainer';
import Data from 'data/general';
import GridContainer from "components/material_ui/Grid/GridContainer.js";
import Parallax from "components/material_ui/Parallax/Parallax.js";
import GridItem from "components/material_ui/Grid/GridItem.js";
import styles from "assets/jss/material-kit-react/views/componentsSections/channelsStyle.js";
import Card from "components/material_ui/Card/Card.js";
import CardBody from "components/material_ui/Card/CardBody.js";

const useStyles = makeStyles(styles);

function GeneralsPage() {
  const classes = useStyles();

  return (
    <div>
      <Parallax image={require("assets/img/backgrounds/5.png")}>
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
                <Grid item xs={2}>
                  <NavigationButtonContainer
                    text={BACK}
                    navigation={CHAINS_PAGE}
                  />
                </Grid>
                <Grid item xs={8} />
                <Grid item xs={2}>
                  <NavigationButtonContainer
                    text={NEXT}
                    navigation={USERS_PAGE}
                  />
                </Grid>
              </Grid>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

export default GeneralsPage;
