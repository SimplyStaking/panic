import React from "react";
// nodejs library to set properties for components
import PropTypes from "prop-types";
// @material-ui/core components
import Snack from "@material-ui/core/SnackbarContent";
import Icon from "@material-ui/core/Icon";
import useStyles from
  "assets/jss/material-kit-react/components/snackbarContentStyle";

export default function SnackbarContent(props) {
  const { message, color, icon, icon_color } = props;
  const classes = useStyles();
  let snackIcon = null;
  switch (typeof icon) {
    case "object":
      snackIcon = <props.icon
                    className={classes.icon} style={{color: icon_color}}/>;
      break;
    case "string":
      snackIcon = <Icon className={classes.icon} style={{color: icon_color}} >{props.icon}</Icon>;
      break;
    default:
      snackIcon = null;
      break;
  }
  return (
    <Snack
      message={
        <div>
          {snackIcon}
          {message}
        </div>
      }
      classes={{
        root: classes.root + " " + classes[color],
        message: classes.message + " " + classes.container
      }}
    />
  );
}

SnackbarContent.propTypes = {
  message: PropTypes.node.isRequired,
  color: PropTypes.oneOf(["default","info", "success", "warning", "danger", "primary"]),
  close: PropTypes.bool,
  icon: PropTypes.oneOfType([PropTypes.object, PropTypes.string]),
  icon_color: PropTypes.string
};
