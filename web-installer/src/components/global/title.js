import React from 'react';
import PropTypes from 'prop-types';
import Typography from '@material-ui/core/Typography';
import Box from '@material-ui/core/Box';

const Title = (props) => {
  const { text } = props;
  return (
    <Box pt={3}>
      <Typography
        style={{ textAlign: 'center' }}
        variant="h2"
        align="center"
        gutterBottom
      >
        {text}
      </Typography>
    </Box>
  );
};

Title.propTypes = {
  text: PropTypes.string.isRequired,
};

export default Title;
