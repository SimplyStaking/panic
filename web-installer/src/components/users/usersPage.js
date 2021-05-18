import React from 'react';
import { Grid, Box, Typography } from '@material-ui/core';
import NavigationButtonContainer from 'containers/global/navigationButtonContainer';
import {
  UsersFormContainer,
  UsersTableContainer,
} from 'containers/users/usersContainer';
import { CHAINS_PAGE, BACK } from 'constants/constants';
import GridContainer from 'components/material_ui/Grid/GridContainer';
import Parallax from 'components/material_ui/Parallax/Parallax';
import GridItem from 'components/material_ui/Grid/GridItem';
import useStyles from 'assets/jss/material-kit-react/views/componentsSections/channelsStyle';
import Card from 'components/material_ui/Card/Card';
import CardBody from 'components/material_ui/Card/CardBody';
import Divider from '@material-ui/core/Divider';
import EndDialog from 'components/users/endDialog';
import Data from 'data/users';
import Background from 'assets/img/backgrounds/background.png';

function UsersPage() {
  const classes = useStyles();

  return (
    <div>
      <Parallax image={Background}>
        <div className={classes.container}>
          <GridContainer>
            <GridItem>
              <div className={classes.brand}>
                <h1 className={classes.title}>{Data.title}</h1>
              </div>
            </GridItem>
          </GridContainer>
        </div>
      </Parallax>
      <div className={classes.mainRaised}>
        <Card>
          <CardBody>
            <div className={classes.container}>
              <div className="greyBackground">
                <Typography variant="subtitle1" gutterBottom>
                  <Box m={2} pt={3} px={3}>
                    <p
                      style={{
                        fontWeight: '350',
                        fontSize: '1.2rem',
                      }}
                    >
                      {Data.description}
                    </p>
                  </Box>
                </Typography>
                <Divider />
                <Box m={2} p={3}>
                  <Grid container spacing={1} justify="center" alignItems="center">
                    <Grid item xs={12}>
                      <Box p={2} className="flex_root">
                        <Box
                          p={3}
                          borderRadius="borderRadius"
                          borderColor="grey.300"
                        >
                          <UsersFormContainer />
                        </Box>
                      </Box>
                    </Grid>
                  </Grid>
                </Box>
              </div>
              <UsersTableContainer />
              <Box py={5}>
                <Grid container spacing={3} justify="center" alignItems="center">
                  <Grid item xs={4} />
                  <Grid item xs={2}>
                    <NavigationButtonContainer
                      text={BACK}
                      navigation={CHAINS_PAGE}
                    />
                  </Grid>
                  <Grid item xs={2}>
                    <EndDialog />
                  </Grid>
                  <Grid item xs={4} />
                </Grid>
              </Box>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

export default UsersPage;
