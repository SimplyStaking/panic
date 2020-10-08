import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import Box from '@material-ui/core/Box';

const MainText = (text) => {
  return (
    <Box p={5} className="greyBackground">
      <p style={{ textAlign: 'justify' }}>
        {text}
      </p>
    </Box>
  );
};

MainText.propTypes = forbidExtraProps({
  text: PropTypes.string.isRequired,
});

export default MainText;
