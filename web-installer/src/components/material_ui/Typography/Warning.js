import React from "react";
// nodejs library to set properties for components
import PropTypes from "prop-types";
// core components
import useStyles from "assets/jss/material-kit-react/components/typographyStyle";

export default function Warning(props) {
  const classes = useStyles();
  const { children } = props;
  return (
    <div className={classes.defaultFontStyle + " " + classes.warningText}>
      {children}
    </div>
  );
}

Warning.propTypes = {
  children: PropTypes.node
};
