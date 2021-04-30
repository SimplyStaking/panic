import React from 'react';
import { Grid } from '@material-ui/core';
import NavigationButtonContainer from 'containers/global/navigationButtonContainer';
import CosmosChainsTableContainer from 'containers/chains/cosmos/cosmosChainsTableContainer';
import SubstrateChainsTableContainer from 'containers/chains/substrate/substrateChainsTableContainer';
import ChainlinkChainsTableContainer from 'containers/chains/chainlink/chainlinkChainsTableContainer';
import CosmosIcon from 'assets/icons/cosmos.png';
import SubstrateIcon from 'assets/icons/substrate.png';
import ChainlinkIcon from 'assets/icons/chainlink.png';
import {
  CHANNELS_PAGE,
  NEXT,
  BACK,
  COSMOS_SETUP_PAGE,
  NEW,
  COSMOS,
  SUBSTRATE,
  SUBSTRATE_SETUP_PAGE,
  USERS_PAGE,
  OTHER,
  OTHER_SETUP_PAGE,
  CONFIGURE,
  CHAINLINK,
  CHAINLINK_SETUP_PAGE,
} from 'constants/constants';
import Data from 'data/chains';
import GridContainer from 'components/material_ui/Grid/GridContainer';
import Parallax from 'components/material_ui/Parallax/Parallax';
import GridItem from 'components/material_ui/Grid/GridItem';
import useStyles from 'assets/jss/material-kit-react/views/componentsSections/channelsStyle';
import Card from 'components/material_ui/Card/Card';
import CardBody from 'components/material_ui/Card/CardBody';
import DescriptionSection from 'components/chains/descriptionSection';
import SystemIcon from 'assets/icons/system.svg';
import Background from 'assets/img/backgrounds/background.png';
import ChainAccordion from './chainAccordion';

/*
 * This page holds all the chain accordions, configured to load a chain setup
 * and the chains already setup.
 */
function Chains() {
  const classes = useStyles();

  return (
    <div>
      <Parallax image={Background}>
        <div className={classes.container}>
          <GridContainer>
            <GridItem>
              <div className={classes.brand}>
                <h1 className={classes.title}>{Data.chains.title}</h1>
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
                      table={<CosmosChainsTableContainer />}
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
                      table={<SubstrateChainsTableContainer />}
                    />
                    <ChainAccordion
                      icon={ChainlinkIcon}
                      name={CHAINLINK}
                      button={(
                        <NavigationButtonContainer
                          text={NEW}
                          navigation={CHAINLINK_SETUP_PAGE}
                        />
                      )}
                      table={<ChainlinkChainsTableContainer />}
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
                      table={<div />}
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

export default Chains;
