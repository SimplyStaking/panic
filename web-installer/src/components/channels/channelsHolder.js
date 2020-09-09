import React from 'react';
import ChannelAccordion from './channelAccordion';
import {
  TELEGRAM, TWILIO, EMAIL, PAGERDUTY, OPSGENIE,
} from '../../constants/constants';
import TelegramIcon from '../../assets/icons/telegram.svg';
import TwilioIcon from '../../assets/icons/twilio.svg';
import EmailIcon from '../../assets/icons/email.svg';
import PagerDuty from '../../assets/icons/pagerduty.svg';
import OpsGenie from '../../assets/icons/opsGenie.svg';
import { TelegramFormContainer, TelegramTableContainer } from '../../containers/channels/telegram_container';
import { TwilioFormContainer, TwilioTableContainer } from '../../containers/channels/twilio_container';
import { EmailFormContainer, EmailTableContainer } from '../../containers/channels/email_container';
import { PagerDutyFormContainer, PagerDutyTableContainer } from '../../containers/channels/pagerDuty_container';
import { OpsGenieFormContainer, OpsGenieTableContainer } from '../../containers/channels/opsGenie_container';

const ChannelsContainer = () => (
  <div>
    <ChannelAccordion
      icon={TelegramIcon}
      name={TELEGRAM}
      form={(<TelegramFormContainer />)}
    />
    <TelegramTableContainer />
    <ChannelAccordion
      icon={TwilioIcon}
      name={TWILIO}
      form={(<TwilioFormContainer />)}
    />
    <TwilioTableContainer />
    <ChannelAccordion
      icon={EmailIcon}
      name={EMAIL}
      form={<EmailFormContainer />}
    />
    <EmailTableContainer />
    <ChannelAccordion
      icon={PagerDuty}
      name={PAGERDUTY}
      form={<PagerDutyFormContainer />}
    />
    <PagerDutyTableContainer />
    <ChannelAccordion
      icon={OpsGenie}
      name={OPSGENIE}
      form={<OpsGenieFormContainer />}
    />
    <OpsGenieTableContainer />
  </div>
);

export default ChannelsContainer;
