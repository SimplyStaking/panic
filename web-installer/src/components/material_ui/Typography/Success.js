import React from 'react';
// nodejs library to set properties for components
import PropTypes from 'prop-types';
// core components
import useStyles from 'assets/jss/material-kit-react/components/typographyStyle';

export default function Success(props) {
  const classes = useStyles();
  const { children } = props;
  return (
    <div className={`${classes.defaultFontStyle} ${classes.successText}`}>
      {children}
    </div>
  );
}

Success.propTypes = {
  children: PropTypes.node,
};
