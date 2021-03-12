import React from 'react';
// nodejs library to set properties for components
import PropTypes from 'prop-types';
// core components
import useStyles from 'assets/jss/material-kit-react/components/typographyStyle';

export default function Muted(props) {
  const classes = useStyles();
  const { children } = props;
  return (
    <div className={`${classes.defaultFontStyle} ${classes.mutedText}`}>
      {children}
    </div>
  );
}

Muted.propTypes = {
  children: PropTypes.node.isRequired,
};
