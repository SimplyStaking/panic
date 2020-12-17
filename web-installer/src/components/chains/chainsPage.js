import React from 'react';
import { makeStyles } from "@material-ui/core/styles";
import { Grid } from '@material-ui/core';
import NavigationButtonContainer from
  'containers/global/navigationButtonContainer';
import CosmosChainsTableContainer from
  'containers/chains/cosmos/cosmosChainsTableContainer';
import SubstrateChainsTableContainer from
  'containers/chains/substrate/substrateChainsTableContainer';
import ChainAccordion from './chainAccordion';
import CosmosIcon from 'assets/icons/cosmos.png';
import SubstrateIcon from 'assets/icons/substrate.png';
import {
  CHANNELS_PAGE, NEXT, BACK, COSMOS_SETUP_PAGE, NEW,
  COSMOS, SUBSTRATE, SUBSTRATE_SETUP_PAGE, GENERAL_PAGE, OTHER,
  OTHER_SETUP_PAGE, CONFIGURE
} from 'constants/constants';
import Data from 'data/chains';
import GridContainer from "components/material_ui/Grid/GridContainer.js";
import Parallax from "components/material_ui/Parallax/Parallax.js";
import GridItem from "components/material_ui/Grid/GridItem.js";
import styles from
  "assets/jss/material-kit-react/views/componentsSections/channelsStyle.js";
import Card from "components/material_ui/Card/Card.js";
import CardBody from "components/material_ui/Card/CardBody.js";
import DescriptionSection from "components/chains/descriptionSection.js";
import SystemIcon from 'assets/icons/system.svg';

const useStyles = makeStyles(styles);

/*
 * This page holds all the chain accordions, configured to load a chain setup
 * and the chains already setup.
 */
function Chains() {
  const classes = useStyles();

  return (
    <div>
      <Parallax image={require("assets/img/backgrounds/5.png")}>
        <div className={classes.container}>
          <GridContainer>
            <GridItem>
              <div className={classes.brand}>
                <h1 className={classes.title}>
                  {Data.chains.title}
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
              <DescriptionSection />
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <div>
                    <ChainAccordion
                      icon={CosmosIcon}
                      name={COSMOS}
                      button={(
                        <NavigationButtonContainer
                          text={NEW}
                          navigation={COSMOS_SETUP_PAGE}
                        />
                      )}
                      table={(<CosmosChainsTableContainer />)}
                    />
                    <ChainAccordion
                      icon={SubstrateIcon}
                      name={SUBSTRATE}
                      button={(
                        <NavigationButtonContainer
                          text={NEW}
                          navigation={SUBSTRATE_SETUP_PAGE}
                        />
                      )}
                      table={(
                        <SubstrateChainsTableContainer />
                      )}
                    />
                    <ChainAccordion
                      icon={SystemIcon}
                      name={OTHER}
                      button={(
                        <NavigationButtonContainer
                          text={CONFIGURE}
                          navigation={OTHER_SETUP_PAGE}
                        />
                      )}
                      table={<div/>}
                    />
                  </div>
                </Grid>
                <Grid item xs={12} />
                <Grid item xs={4} />
                <Grid item xs={2}>
                  <NavigationButtonContainer
                    text={BACK}
                    navigation={CHANNELS_PAGE}
                  />
                </Grid>
                <Grid item xs={2}>
                  <NavigationButtonContainer
                    text={NEXT}
                    navigation={GENERAL_PAGE}
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

export default Chains;
