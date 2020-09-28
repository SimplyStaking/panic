import React from 'react';
import PropTypes from 'prop-types';
import Box from '@material-ui/core/Box';

const MainText = (props) => {
  const { text } = props;
  return (
    <Box p={5} className="greyBackground">
      <p style={{ textAlign: 'justify' }}>
        {text}
      </p>
    </Box>
  );
};

MainText.propTypes = {
  text: PropTypes.string.isRequired,
};

export default MainText;
