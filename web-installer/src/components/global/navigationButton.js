import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import Button from "components/material_ui/CustomButtons/Button.js";

const NavigationButton = ({disabled, navigation, nextPage, buttonText}) => {

  function triggerNextPage(e) {
    e.preventDefault();
    nextPage(navigation);
  }

  return (
    <Button
      onClick={triggerNextPage}
      size="lg"
      color="primary"
      disabled={disabled}
    >
      {buttonText}
    </Button>
  );
};

NavigationButton.propTypes = forbidExtraProps({
  disabled: PropTypes.bool.isRequired,
  navigation: PropTypes.string.isRequired,
  nextPage: PropTypes.func.isRequired,
  buttonText: PropTypes.string.isRequired,
});

export default NavigationButton;
