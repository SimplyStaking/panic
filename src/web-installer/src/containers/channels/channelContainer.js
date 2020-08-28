import React from 'react'
import ChannelAccordion from '../../components/channels/channelAccordion';
import TelegramIcon from '../../assets/icons/telegram.svg';
import TwilioIcon from '../../assets/icons/twilio.svg';
import EmailIcon from '../../assets/icons/email.svg';
import PagerDuty from '../../assets/icons/pagerduty.svg';
import OpsGenie from '../../assets/icons/opsGenie.svg';

function ChannelAccordionsContainer() {
  const Form = <div></div>;

  return (
    <div>
      <ChannelAccordion 
        icon={TelegramIcon}
        name={'Telegram'}
        form={Form}
      />
      <ChannelTable/>
      <ChannelAccordion 
        icon={TwilioIcon}
        name={'Twilio'}
      />
      <ChannelAccordion 
        icon={EmailIcon}
        name={'Email'}
      />
      <ChannelAccordion 
        icon={PagerDuty}
        name={'PagerDuty'}
      />
      <ChannelAccordion 
        icon={OpsGenie}
        name={'OpsGenie'}
      />
    </div>
  )
}

export default ChannelAccordionsContainer;
