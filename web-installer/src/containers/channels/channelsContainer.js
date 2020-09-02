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
import TelegramContainer from './telegram_container';

const ChannelsContainer = () => (
  <div>
    <ChannelAccordion
      icon={TelegramIcon}
      name={TELEGRAM}
      form={(
        <TelegramContainer />
      )}
    />
    <ChannelAccordion
      icon={TwilioIcon}
      name={TWILIO}
      form={(
        <TelegramContainer />
      )}
    />
    <ChannelAccordion
      icon={EmailIcon}
      name={EMAIL}
      form={<TelegramContainer />}
    />
    <ChannelAccordion
      icon={PagerDuty}
      name={PAGERDUTY}
      form={<TelegramContainer />}
    />
    <ChannelAccordion
      icon={OpsGenie}
      name={OPSGENIE}
      form={<TelegramContainer />}
    />
  </div>
);

export default ChannelsContainer;
