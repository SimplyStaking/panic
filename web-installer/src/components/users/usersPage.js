import React from 'react';
import { Grid, Box, Typography } from '@material-ui/core';
import { makeStyles } from "@material-ui/core/styles";
import NavigationButtonContainer from
  'containers/global/navigationButtonContainer';
import { UsersFormContainer, UsersTableContainer } from
  'containers/users/usersContainer';
import { GENERAL_PAGE, BACK } from 'constants/constants';
import GridContainer from "components/material_ui/Grid/GridContainer.js";
import Parallax from "components/material_ui/Parallax/Parallax.js";
import GridItem from "components/material_ui/Grid/GridItem.js";
import styles from
  "assets/jss/material-kit-react/views/componentsSections/channelsStyle.js";
import Card from "components/material_ui/Card/Card.js";
import CardBody from "components/material_ui/Card/CardBody.js";
import Divider from '@material-ui/core/Divider';
import EndDialog from 'components/users/endDialog';
import Data from 'data/users';

const useStyles = makeStyles(styles);

function UsersPage() {
  const classes = useStyles();

  return (
    <div>
      <Parallax image={require("assets/img/backgrounds/5.png")}>
        <div className={classes.container}>
          <GridContainer>
            <GridItem>
              <div className={classes.brand}>
                <h1 className={classes.title}>
                  {Data.title}
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
              <Typography
                variant="subtitle1"
                gutterBottom
                className="greyBackground"
              >
                <Box m={2} p={3}>
                  <p>{Data.description}</p>
                </Box>
              </Typography>
              <Divider />
              <Grid container spacing={0}>
                <Grid item xs={12}>
                  <Box p={2} className="flex_root">
                    <Box
                      p={3}
                      borderRadius="borderRadius"
                      borderColor="grey.300"
                    >
                      <UsersFormContainer />
                      <br />
                      <br />
                      <UsersTableContainer />
                    </Box>
                  </Box>
                </Grid>
                <Grid item xs={12} />
                <br />
                <br />
                <Grid item xs={4} />
                <Grid item xs={2}>
                  <NavigationButtonContainer
                    text={BACK}
                    navigation={GENERAL_PAGE}
                  />
                </Grid>
                <Grid item xs={2}>
                  <EndDialog />
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

export default UsersPage;
