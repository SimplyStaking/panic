import React from 'react';
// @material-ui/core components
import { makeStyles } from '@material-ui/core/styles';
// @material-ui/icons
import Warning from '@material-ui/icons/Warning';
// core components
import SnackbarContent from 'components/material_ui/Snackbar/SnackbarContent.js';
import Clearfix from 'components/material_ui/Clearfix/Clearfix.js';
import NewReleasesIcon from '@material-ui/icons/NewReleases';
import styles from 'assets/jss/material-kit-react/views/componentsSections/notificationsStyles.js';
import ErrorIcon from '@material-ui/icons/Error';
import Data from 'data/channels';

const useStyles = makeStyles(styles);

export default function AlertsSection() {
  const classes = useStyles();
  return (
    <div className={classes.section} id="notifications">
      <SnackbarContent
        message={(
          <span>
            <b>{Data.alerts.info}</b>
          </span>
        )}
        color="default"
        icon="info_outline"
        icon_color="#339900"
      />
      <SnackbarContent
        message={(
          <span>
            <b>{Data.alerts.warning}</b>
          </span>
        )}
        color="default"
        icon={Warning}
        icon_color="#EED202"
      />
      <SnackbarContent
        message={(
          <span>
            <b>{Data.alerts.critical}</b>
          </span>
        )}
        color="default"
        icon={NewReleasesIcon}
        icon_color="#cc3300"
      />
      <SnackbarContent
        message={(
          <span>
            <b>{Data.alerts.error}</b>
          </span>
        )}
        color="default"
        icon={ErrorIcon}
        icon_color="#000000"
      />
      <Clearfix />
    </div>
  );
}
