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
import TelegramForm from './telegramForm';

const ChannelsContainer = () => (
  <div>
    <ChannelAccordion
      icon={TelegramIcon}
      name={TELEGRAM}
      form={(
        <TelegramForm />
      )}
    />
    <ChannelAccordion
      icon={TwilioIcon}
      name={TWILIO}
      form={(
        <TelegramForm />
      )}
    />
    <ChannelAccordion
      icon={EmailIcon}
      name={EMAIL}
      form={<TelegramForm />}
    />
    <ChannelAccordion
      icon={PagerDuty}
      name={PAGERDUTY}
      form={<TelegramForm />}
    />
    <ChannelAccordion
      icon={OpsGenie}
      name={OPSGENIE}
      form={<TelegramForm />}
    />
  </div>
);

export default ChannelsContainer;
