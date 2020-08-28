import React from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import Welcome from '../pages/welcome';
import Channels from '../pages/channels';

import { WELCOME_PAGE, CHANNELS_PAGE } from '../constants/pages';

const mapStateToProps = (state) => ({ page: state.ChangePageReducer.page });

// Returns the specific page according to pre-set pages
function getPage(pageName) {
  switch (pageName) {
    case WELCOME_PAGE:
      return <Welcome />;
    case CHANNELS_PAGE:
      return <Channels />;
    default:
      return <Welcome />;
  }
}

// Page Selector changes according to the global page set
function PageSelector(props) {
  const { page } = props;
  return (
    <div>
      {getPage(page)}
    </div>
  );
}

PageSelector.propTypes = {
  page: PropTypes.string.isRequired,
};

export default connect(mapStateToProps)(PageSelector);
