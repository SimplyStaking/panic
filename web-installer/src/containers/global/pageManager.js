import React, { Component } from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { ToastsStore } from 'react-toasts';
import WelcomePage from 'components/welcome/welcomePage';
import ChannelsPage from 'components/channels/channelsPage';
import ChainsPage from 'components/chains/chainsPage';
import CosmosSetupPage from 'components/chains/cosmos/cosmosSetupPage';
import SubstrateSetupPage from 'components/chains/substrate/substrateSetupPage';
import ChainlinkSetupPage from 'components/chains/chainlink/chainlinkSetupPage';
import GeneralSetupPage from 'components/chains/general/generalSetupPage';
import UsersPage from 'components/users/usersPage';
import {
  WELCOME_PAGE,
  CHANNELS_PAGE,
  CHAINS_PAGE,
  COSMOS_SETUP_PAGE,
  SUBSTRATE_SETUP_PAGE,
  USERS_PAGE,
  GENERAL_SETUP_PAGE,
  CHAINLINK_SETUP_PAGE,
} from 'constants/constants';
import { refreshAccessToken } from 'utils/data';

const mapStateToProps = (state) => ({
  page: state.ChangePageReducer.page,
  authenticated: state.LoginReducer.authenticated,
});

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
    case CHAINLINK_SETUP_PAGE:
      return <ChainlinkSetupPage />;
    case GENERAL_SETUP_PAGE:
      return <GeneralSetupPage />;
    case USERS_PAGE:
      return <UsersPage />;
    default:
      return <WelcomePage />;
  }
}

class PageManager extends Component {
  constructor(props) {
    super(props);
    this.dataTimer = null;
  }

  // This is used to refresh the JWT token
  componentDidMount() {
    this.refreshToken();
    this.dataTimer = setInterval(this.refreshToken.bind(this), 10000);
  }

  componentWillUnmount() {
    clearInterval(this.dataTimer);
    this.dataTimer = null;
  }

  // eslint-disable-next-line class-methods-use-this
  async refreshToken() {
    const { authenticated } = this.props;
    if (authenticated) {
      try {
        await refreshAccessToken();
      } catch (e) {
        if (e.response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          ToastsStore.error(
            `Could not get authentication status. Error: ${e.response.data.error}`,
            5000,
          );
        } else {
          // Something happened in setting up the request that triggered an
          // error
          ToastsStore.error(
            `Could not get authentication status. Error: ${e.message}`,
            5000,
          );
        }
      }
    }
  }

  render() {
    const { page } = this.props;
    return <div>{getPage(page)}</div>;
  }
}

PageManager.propTypes = {
  page: PropTypes.string.isRequired,
  authenticated: PropTypes.bool.isRequired,
};

export default connect(mapStateToProps)(PageManager);
