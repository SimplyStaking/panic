import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import { Button, Box } from '@material-ui/core';

const NavigationButton = ({navigation, nextPage, buttonText}) => {

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

NavigationButton.propTypes = forbidExtraProps({
  navigation: PropTypes.string.isRequired,
  nextPage: PropTypes.func.isRequired,
  buttonText: PropTypes.string.isRequired,
});

export default NavigationButton;
