/* eslint-disable no-unused-vars */
import React from 'react';
import { Grid, Box } from '@material-ui/core';
import NavigationButtonContainer from 'containers/global/navigationButtonContainer';
import CosmosChainsTableContainer from 'containers/chains/cosmos/cosmosChainsTableContainer';
import SubstrateChainsTableContainer from 'containers/chains/substrate/substrateChainsTableContainer';
import ChainlinkChainsTableContainer from 'containers/chains/chainlink/chainlinkChainsTableContainer';
import CosmosIcon from 'assets/icons/cosmos-atom-logo.svg';
import SubstrateIcon from 'assets/icons/Substrate-logo.svg';
import ChainlinkIcon from 'assets/icons/chainlink-link-logo.svg';
import {
  CHANNELS_PAGE,
  NEXT,
  BACK,
  COSMOS_SETUP_PAGE,
  SUBSTRATE_SETUP_PAGE,
  USERS_PAGE,
  OTHER_SETUP_PAGE,
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
import CustomParticles from 'components/material_ui/Particles/CoverBlockchainParticles.js';
import ChainAccordion from './chainAccordion';

/*
 * This page holds all the chain accordions, configured to load a chain setup
 * and the chains already setup.
 */
function Chains() {
  const classes = useStyles();

  return (
    <div>
      <Parallax>
        <CustomParticles />
        <div
          style={{
            position: 'absolute',
            display: 'block',
            width: '100%',
            height: '100%',
            background: 'black',
            opacity: '0.8',
            top: '0',
          }}
        />
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
          }}
        >
          <div className={classes.container}>
            <GridContainer>
              <GridItem>
                <div className={classes.brand}>
                  <h1 className={classes.title}>{Data.chains.title}</h1>
                </div>
              </GridItem>
            </GridContainer>
          </div>
        </div>
      </Parallax>
      <div className={classes.mainRaised}>
        <Card>
          <CardBody>
            <div className={classes.container}>
              <DescriptionSection />
              <Grid container spacing={0}>
                <Grid item xs={12}>
                  <ChainAccordion
                    icon={CosmosIcon}
                    name="Cosmos-based Blockchain Setup"
                    button={(
                      <NavigationButtonContainer
                        text="Configure a new Cosmos-based Blockchain"
                        navigation={COSMOS_SETUP_PAGE}
                      />
                    )}
                    table={<CosmosChainsTableContainer />}
                  />
                </Grid>
                <Grid item xs={12}>
                  <ChainAccordion
                    icon={SubstrateIcon}
                    name="Substrate-based Blockchain Setup"
                    button={(
                      <NavigationButtonContainer
                        text="Configure a new Substrate-based Blockchain"
                        navigation={SUBSTRATE_SETUP_PAGE}
                      />
                    )}
                    table={<SubstrateChainsTableContainer />}
                  />
                </Grid>
                <Grid item xs={12}>
                  <ChainAccordion
                    icon={ChainlinkIcon}
                    name="Chainlink Node Setup"
                    button={(
                      <NavigationButtonContainer
                        text="Configure a new chain and Chainlink Nodes"
                        navigation={CHAINLINK_SETUP_PAGE}
                      />
                    )}
                    table={<ChainlinkChainsTableContainer />}
                  />
                </Grid>
                <Grid item xs={12}>
                  <ChainAccordion
                    icon={SystemIcon}
                    name="General Sources Setup"
                    button={(
                      <NavigationButtonContainer
                        text="Configure General Source of data you want monitored"
                        navigation={OTHER_SETUP_PAGE}
                      />
                    )}
                    table={<div />}
                  />
                </Grid>
                <Grid container spacing={4}>
                  <Grid item xs={4} />
                  <Grid item xs={2}>
                    <Box py={4}>
                      <NavigationButtonContainer text={BACK} navigation={CHANNELS_PAGE} />
                    </Box>
                  </Grid>
                  <Grid item xs={2}>
                    <Box py={4}>
                      <NavigationButtonContainer text={NEXT} navigation={USERS_PAGE} />
                    </Box>
                  </Grid>
                  <Grid item xs={4} />
                </Grid>
              </Grid>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

export default Chains;
