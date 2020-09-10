import React from 'react';
import PropTypes from 'prop-types';
import { Button, Box } from '@material-ui/core';

const NavigationButton = (props) => {
  const {
    buttonText, navigation, nextPage, disabled,
  } = props;

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
        disabled={disabled}
        color="primary"
      >
        {buttonText}
      </Button>
    </Box>
  );
};

NavigationButton.propTypes = {
  disabled: PropTypes.bool.isRequired,
  buttonText: PropTypes.string.isRequired,
  navigation: PropTypes.string.isRequired,
  nextPage: PropTypes.func.isRequired,
};

export default NavigationButton;
