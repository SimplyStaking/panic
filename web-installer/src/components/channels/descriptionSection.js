import React from "react";
// @material-ui/core components
import { makeStyles } from "@material-ui/core/styles";

// @material-ui/icons
import HelpIcon from '@material-ui/icons/Help';
import SettingsIcon from '@material-ui/icons/Settings';
import AddIcCallIcon from '@material-ui/icons/AddIcCall';
// core components
import GridContainer from "components/material_ui/Grid/GridContainer.js";
import GridItem from "components/material_ui/Grid/GridItem.js";
import InfoArea from "components/material_ui/InfoArea/InfoArea.js";
import Data from 'data/channels';
import AlertSection from "components/channels/alertSection.js";
import styles from "assets/jss/material-kit-react/views/landingPageSections/productStyle.js";

const useStyles = makeStyles(styles);

export default function DescriptionSection() {
  const classes = useStyles();
  return (
    <div className={classes.section}>
      <GridContainer justify="center">
        <GridItem xs={12} sm={12} md={8}>
          <h1 className={classes.title}>
              Everything you need to know about Channels.
          </h1>
        </GridItem>
      </GridContainer>
      <div>
        <GridContainer>
          <GridItem xs={12} sm={12} md={4}>
            <InfoArea
              title={Data.channels.what_title}
              description={Data.channels.what}
              icon={HelpIcon}
              iconColor="#00000"
              vertical
            />
          </GridItem>
          <GridItem xs={12} sm={12} md={4}>
            <InfoArea
              title={Data.channels.why_title}
              description={Data.channels.why}
              icon={AddIcCallIcon}
              iconColor="#00000"
              vertical
            />
          </GridItem>
          <GridItem xs={12} sm={12} md={4}>
            <InfoArea
              title={Data.channels.how_title}
              description={Data.channels.how}
              icon={SettingsIcon}
              iconColor="#00000"
              vertical
            />
          </GridItem>
        </GridContainer>
        <GridContainer>
          <GridItem xs={12} sm={12} md={12}>
            <h1 className={classes.title}>
              Types of Alerts
            </h1>
            <br></br>
          </GridItem>
        </GridContainer>
        <AlertSection />
      </div>
    </div>
  );
}
