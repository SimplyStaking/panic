import React from 'react';
import { makeStyles } from '@material-ui/core/styles';
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
import SystemIcon from '../../assets/icons/system.svg';
import {
  CHANNELS_PAGE, DONE, BACK, COSMOS_SETUP_PAGE, NEW, CONFIGURE,
  COSMOS, SUBSTRATE, SUBSTRATE_SETUP_PAGE, GENERAL_PAGE, GENERAL_SETUP_PAGE,
  GENERAL,
} from '../../constants/constants';
import Data from '../../data/chains';

const useStyles = makeStyles((theme) => ({
  root: {
    flexGrow: 1,
  },
  paper: {
    padding: theme.spacing(2),
    textAlign: 'center',
    color: theme.palette.text.primary,
  },
  icon: {
    paddingRight: '1rem',
  },
  heading: {
    fontSize: theme.typography.pxToRem(15),
    fontWeight: theme.typography.fontWeightRegular,
  },
}));

function Chains() {
  const classes = useStyles();

  return (
    <div>
      <Title
        text={Data.chains.title}
      />
      <MainText
        text={Data.chains.description}
      />
      <Box p={2} className={classes.root}>
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
          <ChainAccordion
            icon={SystemIcon}
            name={GENERAL}
            button={(
              <NavigationButtonContainer
                text={CONFIGURE}
                navigation={GENERAL_SETUP_PAGE}
              />
            )}
            table={(<div />)}
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
