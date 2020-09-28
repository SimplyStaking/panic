import React from 'react';
import PropTypes from 'prop-types';
import { Button, Box } from '@material-ui/core';

const NavigationButton = (props) => {
  const { navigation, nextPage, buttonText } = props;

  function triggerNextPage(e) {
    e.preventDefault();
    nextPage(navigation);
  }

  return (
    <Box p={5} style={{ float: 'right' }}>
      <Button
        onClick={triggerNextPage}
        size="large"
        variant="outlined"
        color="primary"
      >
        {buttonText}
      </Button>
    </Box>
  );
};

NavigationButton.propTypes = {
  navigation: PropTypes.string.isRequired,
  nextPage: PropTypes.func.isRequired,
  buttonText: PropTypes.string.isRequired,
};

export default NavigationButton;
