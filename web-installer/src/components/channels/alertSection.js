import React from "react";
// @material-ui/core components
import { makeStyles } from "@material-ui/core/styles";
// @material-ui/icons
import Check from "@material-ui/icons/Check";
import Warning from "@material-ui/icons/Warning";
// core components
import SnackbarContent from "components/material_ui/Snackbar/SnackbarContent.js";
import Clearfix from "components/material_ui/Clearfix/Clearfix.js";
import NewReleasesIcon from '@material-ui/icons/NewReleases';
import styles from "assets/jss/material-kit-react/views/componentsSections/notificationsStyles.js";
import ErrorIcon from '@material-ui/icons/Error';
const useStyles = makeStyles(styles);

export default function AlertsSection() {
  const classes = useStyles();
  return (
    <div className={classes.section} id="notifications">
      <SnackbarContent
        message={
          <span>
            <b>INFO ALERT: little to zero severity but consists of information which is still important to acknowledge. Info alerts also include positive events.</b>
          </span>
        }
        color="default"
        icon="info_outline"
      />
      <SnackbarContent
        message={
          <span>
            <b>WARNING ALERT: a less severe alert but which still requires attention as it may be a warning of an incoming critical alert.  </b>
          </span>
        }
        color="default"
        icon={Warning}
      />
      <SnackbarContent
        message={
          <span>
            <b>CRITICAL ALERT: the most severe alert and the type of alert that uses should use Twilio/PagerDuty/OpsGenie phone calling.</b> 
          </span>
        }
        color="default"
        icon={NewReleasesIcon}
      />
      <SnackbarContent
        message={
          <span>
            <b>ERROR ALERT: This is a severe alert which indicates that something is wrong with PANIC.</b> 
          </span>
        }
        color="default"
        icon={ErrorIcon}
      />
      <Clearfix />
    </div>
  );
}
