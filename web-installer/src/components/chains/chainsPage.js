import React from 'react';
import { Box } from '@material-ui/core';
import Title from '../global/title';
import MainText from '../global/mainText';
import NavigationButtonContainer from
  '../../containers/global/navigationButtonContainer';
import CosmosChainsTableContainer from
  '../../containers/chains/cosmos/cosmosChainsTableContainer';
import SubstrateChainsTableContainer from
  '../../containers/chains/substrate/substrateChainsTableContainer';
import ChainAccordion from './chainAccordion';
import CosmosIcon from '../../assets/icons/cosmos.png';
import SubstrateIcon from '../../assets/icons/substrate.png';
import {
  CHANNELS_PAGE, DONE, BACK, COSMOS_SETUP_PAGE, NEW,
  COSMOS, SUBSTRATE, SUBSTRATE_SETUP_PAGE, GENERAL_PAGE,
} from '../../constants/constants';
import Data from '../../data/chains';

/*
 * This page holds all the chain accordions, configured to load a chain setup
 * and the chains already setup.
 */
function Chains() {
  return (
    <div>
      <Title
        text={Data.chains.title}
      />
      <MainText
        text={Data.chains.description}
      />
      <Box p={2} className="flex_root">
        <Box
          p={3}
          border={1}
          borderRadius="borderRadius"
          borderColor="grey.300"
        >
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
        </Box>
      </Box>
      <NavigationButtonContainer
        text={DONE}
        navigation={GENERAL_PAGE}
      />
      <NavigationButtonContainer
        text={BACK}
        navigation={CHANNELS_PAGE}
      />
    </div>
  );
}

export default Chains;
