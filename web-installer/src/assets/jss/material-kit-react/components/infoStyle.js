import {
  primaryColor,
  warningColor,
  dangerColor,
  successColor,
  infoColor,
  roseColor,
  grayColor,
} from "assets/jss/material-kit-react.js";
import { makeStyles } from '@material-ui/core/styles';

const infoStyle = {
  infoArea: {
    maxWidth: "360px",
    margin: "0 auto",
    padding: "0px"
  },
  iconWrapper: {
    float: "left",
    marginTop: "24px",
    marginRight: "10px"
  },
  primary: {
    color: primaryColor
  },
  warning: {
    color: warningColor
  },
  danger: {
    color: dangerColor
  },
  success: {
    color: successColor
  },
  info: {
    color: infoColor
  },
  rose: {
    color: roseColor
  },
  gray: {
    color: grayColor
  },
  icon: {
    width: "36px",
    height: "36px"
  },
  descriptionWrapper: {
    color: grayColor,
    overflow: "hidden"
  },
  title:{
    fontSize: 'large',
    color: '#000000',
  },
  description: {
    color: grayColor,
    overflow: "hidden",
    textAlign: "left",
    marginTop: "0px",
    fontSize: "large",
  },
  iconWrapperVertical: {
    float: "none"
  },
  iconVertical: {
    width: "61px",
    height: "61px"
  }
};

export default makeStyles(infoStyle);
