import React from 'react';
import { Grid } from '@material-ui/core';
import { makeStyles } from "@material-ui/core/styles";
import FormAccordion from 'components/global/formAccordion';
import TelegramIcon from 'assets/icons/telegram.svg';
import TwilioIcon from 'assets/icons/twilio.svg';
import EmailIcon from 'assets/icons/email.svg';
import PagerDuty from 'assets/icons/pagerduty.svg';
import OpsGenie from 'assets/icons/opsGenie.svg';
import { TelegramFormContainer, TelegramTableContainer } from
  'containers/channels/telegramContainer';
import { TwilioFormContainer, TwilioTableContainer } from
  'containers/channels/twilioContainer';
import { EmailFormContainer, EmailTableContainer } from
  'containers/channels/emailContainer';
import { PagerDutyFormContainer, PagerDutyTableContainer } from
  'containers/channels/pagerDutyContainer';
import { OpsGenieFormContainer, OpsGenieTableContainer } from
  'containers/channels/opsGenieContainer';
import NavigationButtonContainer from
  'containers/global/navigationButtonContainer';
import {
  WELCOME_PAGE, CHAINS_PAGE, NEXT, BACK, TELEGRAM, TWILIO, EMAIL,
  PAGERDUTY, OPSGENIE,
} from 'constants/constants';
import Data from 'data/channels';
import GridContainer from "components/material_ui/Grid/GridContainer.js";
import GridItem from "components/material_ui/Grid/GridItem.js";
import Card from "components/material_ui/Card/Card.js";
import CardBody from "components/material_ui/Card/CardBody.js";
import styles from
  "assets/jss/material-kit-react/views/componentsSections/channelsStyle.js";
import Parallax from "components/material_ui/Parallax/Parallax.js";
import DescriptionSection from "components/channels/descriptionSection.js";

const useStyles = makeStyles(styles);

function ChannelsPage() {
  const classes = useStyles();

  return (
    <div>
      <Parallax image={require("assets/img/backgrounds/5.png")}>
        <div className={classes.container}>
          <GridContainer>
            <GridItem>
              <div className={classes.brand}>
                <h1 className={classes.title}>
                  {Data.channels.title}
                </h1>
              </div>
            </GridItem>
          </GridContainer>
        </div>
      </Parallax>
      <div className={classes.mainRaised}>
      <Card>
        <CardBody>
          <div className={classes.container}>
            <DescriptionSection />
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <div>
                  <FormAccordion
                    icon={TelegramIcon}
                    name={TELEGRAM}
                    form={(<TelegramFormContainer />)}
                    table={(<TelegramTableContainer />)}
                  />
                  <FormAccordion
                    icon={TwilioIcon}
                    name={TWILIO}
                    form={(<TwilioFormContainer />)}
                    table={(<TwilioTableContainer />)}
                  />
                  <FormAccordion
                    icon={EmailIcon}
                    name={EMAIL}
                    form={<EmailFormContainer />}
                    table={(<EmailTableContainer />)}
                  />
                  <FormAccordion
                    icon={PagerDuty}
                    name={PAGERDUTY}
                    form={<PagerDutyFormContainer />}
                    table={<PagerDutyTableContainer />}
                  />
                  <FormAccordion
                    icon={OpsGenie}
                    name={OPSGENIE}
                    form={<OpsGenieFormContainer />}
                    table={<OpsGenieTableContainer />}
                  />
                </div>
              </Grid>
              <Grid item xs={12} />
              <Grid item xs={4} />
              <Grid item xs={2}>
                <NavigationButtonContainer
                  text={BACK}
                  navigation={WELCOME_PAGE}
                />
              </Grid>
              <Grid item xs={2}>
                <NavigationButtonContainer
                  text={NEXT}
                  navigation={CHAINS_PAGE}
                />
              </Grid>
              <Grid item xs={4} />
              <Grid item xs={12} />
              </Grid>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

export default ChannelsPage;
