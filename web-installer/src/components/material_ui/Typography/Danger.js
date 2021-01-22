import React from "react";
// nodejs library to set properties for components
import PropTypes from "prop-types";
// core components
import useStyles from "assets/jss/material-kit-react/components/typographyStyle";

export default function Danger(props) {
  const classes = useStyles();
  const { children } = props;
  return (
    <div className={classes.defaultFontStyle + " " + classes.dangerText}>
      {children}
    </div>
  );
}

Danger.propTypes = {
  children: PropTypes.node
};
