import React from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import WelcomePage from '../../components/welcome/welcomePage';
import ChannelsPage from '../../components/channels/channelsPage';
import ChainsPage from '../../components/chains/chainsPage';
import CosmosSetupPage from '../../components/chains/cosmos/cosmosSetupPage';
import SubstrateSetupPage from '../../components/chains/substrate/substrateSetupPage';

import {
  WELCOME_PAGE, CHANNELS_PAGE, CHAINS_PAGE, COSMOS_SETUP_PAGE,
  SUBSTRATE_SETUP_PAGE, GENERAL_PAGE, USERS_PAGE,
} from '../../constants/constants';

const mapStateToProps = (state) => ({ page: state.ChangePageReducer.page });

// Returns the specific page according to pre-set pages
function getPage(pageName) {
  switch (pageName) {
    case WELCOME_PAGE:
      return <WelcomePage />;
    case CHANNELS_PAGE:
      return <ChannelsPage />;
    case CHAINS_PAGE:
      return <ChainsPage />;
    case COSMOS_SETUP_PAGE:
      return <CosmosSetupPage />;
    case SUBSTRATE_SETUP_PAGE:
      return <SubstrateSetupPage />;
    case USERS_PAGE:
      return <SubstrateSetupPage />;
    case GENERAL_PAGE:
      return <SubstrateSetupPage />;
    default:
      return <WelcomePage />;
  }
}

// Page Selector changes according to the global page set
function PageManger(props) {
  const { page } = props;
  return (
    <div>
      {getPage(page)}
    </div>
  );
}

PageManger.propTypes = {
  page: PropTypes.string.isRequired,
};

export default connect(mapStateToProps)(PageManger);
