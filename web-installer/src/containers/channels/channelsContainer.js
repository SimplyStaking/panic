import React from 'react';
import ChannelAccordion from '../../components/channels/channelAccordion';
import {
  TELEGRAM, TWILIO, EMAIL, PAGERDUTY, OPSGENIE,
} from '../../constants/constants';
import TelegramIcon from '../../assets/icons/telegram.svg';
import TwilioIcon from '../../assets/icons/twilio.svg';
import EmailIcon from '../../assets/icons/email.svg';
import PagerDuty from '../../assets/icons/pagerduty.svg';
import OpsGenie from '../../assets/icons/opsGenie.svg';
import { TelegramFormContainer, TelegramTableContainer } from './telegram_container';
import { TwilioFormContainer, TwilioTableContainer } from './twilio_container';

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
      form={<TelegramFormContainer />}
    />
    <ChannelAccordion
      icon={PagerDuty}
      name={PAGERDUTY}
      form={<TelegramFormContainer />}
    />
    <ChannelAccordion
      icon={OpsGenie}
      name={OPSGENIE}
      form={<TelegramFormContainer />}
    />
  </div>
);

export default ChannelsContainer;
