import React from 'react';
import { Grid, Box } from '@material-ui/core';
import { makeStyles } from '@material-ui/core/styles';
import Title from '../global/title';
import MainText from '../global/mainText';
import FormAccordion from '../global/formAccordion';
import TelegramIcon from '../../assets/icons/telegram.svg';
import TwilioIcon from '../../assets/icons/twilio.svg';
import EmailIcon from '../../assets/icons/email.svg';
import PagerDuty from '../../assets/icons/pagerduty.svg';
import OpsGenie from '../../assets/icons/opsGenie.svg';
import { TelegramFormContainer, TelegramTableContainer } from '../../containers/channels/telegramContainer';
import { TwilioFormContainer, TwilioTableContainer } from '../../containers/channels/twilioContainer';
import { EmailFormContainer, EmailTableContainer } from '../../containers/channels/emailContainer';
import { PagerDutyFormContainer, PagerDutyTableContainer } from '../../containers/channels/pagerDutyContainer';
import { OpsGenieFormContainer, OpsGenieTableContainer } from '../../containers/channels/opsGenieContainer';
import NavigationButtonContainer from '../../containers/global/navigationButtonContainer';

import {
  WELCOME_PAGE, CHAINS_PAGE, NEXT, BACK, TELEGRAM, TWILIO, EMAIL,
  PAGERDUTY, OPSGENIE,
} from '../../constants/constants';
import Data from '../../data/channels';

const useStyles = makeStyles((theme) => ({
  root: {
    flexGrow: 1,
  },
  paper: {
    padding: theme.spacing(2),
    textAlign: 'center',
    color: theme.palette.text.primary,
  },
  icon: {
    paddingRight: '1rem',
  },
  heading: {
    fontSize: theme.typography.pxToRem(15),
    fontWeight: theme.typography.fontWeightRegular,
  },
}));

function ChannelsPage() {
  const classes = useStyles();

  return (
    <div>
      <Title
        text={Data.channels.title}
      />
      <MainText
        text={Data.channels.description}
      />
      <Box p={2} className={classes.root}>
        <Box
          p={3}
          border={1}
          borderRadius="borderRadius"
          borderColor="grey.300"
        >
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
          </Grid>
        </Box>
      </Box>
      <NavigationButtonContainer
        text={NEXT}
        navigation={CHAINS_PAGE}
      />
      <NavigationButtonContainer
        text={BACK}
        navigation={WELCOME_PAGE}
      />
    </div>
  );
}

export default ChannelsPage;
