export default {
  channels: {
    title: 'Channel Setup',
    subtitle_1: 'Everything you need to know about Channels.',
    subtitle_2: 'Channel Configuration',
    what_title: 'What are Channels?',
    supported_title: 'Supported Channels',
    how_title: 'How are they setup?',
    what_1: "Channels are used by PANIC to communicate with it's users.",
    what_2: `Channels allow for different modes of communication such as 
      directly calling your phone, or sending messages on Telegram.`,
    what_3: `Channels such as Telegram allow for commands to be inputted. This 
      enables user interaction with the alerter.`,
    channel_1: `Telegram: a cross-platform cloud-based instant messaging, video 
      calling, and VoIP service.`,
    channel_2: `Twilio: allows software developers to programmatically make and 
      receive phone calls.`,
    channel_3: 'PagerDuty: a SaaS incident response platform for IT departments.',
    channel_4: `OpsGenie: an advanced incident response orchestration platform 
      for DevOps and IT Teams.`,
    channel_5: `Email: this can either be a private email server or one 
      provided by a company such as Google.`,
    how_1: `Channels can be setup in the section below, you can configure as 
      many channels as you want.`,
    how_2: `Once a channel is created it can be assigned to any blockchain you 
      want later on during the blockchain setup.`,
    how_3: `Channels can be assigned to multiple blockchains for example multiple 
      chains can send alerts to the same Telegram bot.`,
    how_4: `For each channel, you have  the option to select different alert severities 
      levels. These selections will indicate which alerts the channel is 
      going to receive.`,
  },
  alerts: {
    title: 'Types of Alerts',
    info: `INFO: Alerts of this type have little to zero severity but consists of information 
      which is still important to acknowledge. Info alerts also include positive events. 
      Example: System's storage usage is no longer at a critical level.`,
    warning: `WARNING: A less severe alert type but which still requires attention as it may be a 
      warning of an incoming critical alert. Example: System's storage usage reached 85%.`,
    critical: `CRITICAL: Alerts of this type are the most severe. Such alerts are raised to inform the 
      node operator of a situation which requires immediate action. Example: 
      System's storage usage reached 100%.`,
    error: `ERROR: Alerts of this type are triggered by abnormal events and ranges from zero to high 
      severity based on the error that has occurred and how many times it is triggered. 
      Example: Cannot access GitHub page alert.`,
  },
  telegram: {
    description: `Alerts sent via Telegram are a fast and reliable means of alerting 
      that we highly recommend setting up. This requires you to have a 
      Telegram bot set up, which is a free and quick procedure. Telegram is 
      also used as a two-way interface with the alerter and 
      as an assistant, allowing you to do things such as mute phone 
      call alerts and to get the alerter's current status.`,
    name: 'This will be used to identify the saved telegram configuration.',
    token: 'This is the API token of your created bot.',
    chat_id: 'This is the chat identifier of your newly created bot.',
    severities: 'Severities dictate which alerts will be sent to your chat.',
    commands: 'This will enable commands to be sent from telegram to PANIC.',
    alerts: 'This will enable alerts to be sent from PANIC to telegram.',
    channelNamePlaceholder: 'telegram_chat_1',
    botTokenPlaceholder: 'YOUR BOT TOKEN HERE',
    chatIdPlaceholder: 'YOUR CHAT ID HERE',
  },
  slack: {
    description: `Alerts sent via Slack are a fast and reliable means of alerting 
      that we highly recommend setting up. This requires you to have a 
      Slack bot set up, which is a free and quick procedure. Slack is 
      also used as a two-way interface with the alerter and 
      as an assistant, allowing you to do things such as mute phone 
      call alerts and to get the alerter's current status.`,
    name: 'This will be used to identify the saved slack configuration.',
    botToken: 'This is the Bot User OAuth Token of your created bot.',
    appToken: 'This is the App-Level Token of your created bot.',
    botChannelId: 'This is the ID of the channel which contains your created bot.',
    severities: 'Severities dictate which alerts will be sent to your chat.',
    commands: 'This will enable commands to be sent from slack to PANIC.',
    alerts: 'This will enable alerts to be sent from PANIC to slack.',
    channelNamePlaceholder: 'slack_channel_1',
    botTokenPlaceholder: 'YOUR BOT TOKEN HERE',
    appTokenPlaceholder: 'YOUR APP TOKEN HERE',
    botChannelIdPlaceholder: 'YOUR BOT CHANNEL ID HERE',
  },
  twilio: {
    description: `Twilio phone-call alerts are the most important alerts since they 
      are the best at grabbing your attention, especially when you're 
      asleep! To set these up you have to have a Twilio account set up 
      with a registered Twilio phone number and a verified phone number. 
      The timed trial version of Twilio is free.`,
    name: 'This will be used to identify the saved Twilio configuration.',
    account: 'This is the account SID which can be found on your twilio dashboard.',
    token: 'This is the authentication token which can be found on your twilio dashboard.',
    phoneNumber: 'This is your twilio phone number which will be alerting you.',
    dialNumbers:
      'These are the numbers configured in twilio, which will be called on critical alerts.',
    channelNamePlaceholder: 'twilio-main',
    accountSidPlaceholder: 'YOUR ACCOUNT SID HERE',
    authTokenPlaceholder: 'YOUR AUTHENTICATION TOKEN HERE',
    twilioNumberPlaceholder: 'TWILIO PHONE NUMBER HERE',
    twilioPhoneNumbersToDialValid: 'Add Phone Numbers [Press Enter after each Number]',
  },
  email: {
    description: `Email alerts are more useful as a backup alerting channel rather 
      than the main one, given that one is much more likely to notice a 
      a message on Telegram or a phone call. Email alerts also require 
      an SMTP server to be set up for the alerter to be able to send alerts.`,
    port: `This is the port number at which the SMTP server can be accessed 
      through. Normally this is port number 25 but it would vary depending 
      on your email server setup.`,
    smtp: "This is the SMTP server's address, which is used to send the emails.",
    name: 'This will be used to identify the saved email configuration.',
    from: 'This is the email address that will be sending you the alerts.',
    to: 'These are the email addresses which will be notified on set alerts.',
    username: 'The username used for SMTP authentication.',
    password: 'The password used for SMTP authentication.',
    severities: 'Severities dictate which alerts will be sent to your email.',
    channelNamePlaceholder: 'main_email_channel',
    smtpPlaceholder: 'my.smtp.com',
    portPlaceholder: '25',
    emailFromPlaceHolder: 'alerter@email.com',
    emailsToPlaceHolder: 'Add a destination email [Press Enter after each Email].',
    usernamePlaceHolder: 'my_username',
    passwordPlaceHolder: '*****************',
  },
  pagerDuty: {
    description: `PagerDuty is an incident management platform that provides reliable 
      notifications, automatic escalations, on-call scheduling, and other functionality 
      to help teams detect and fix infrastructure problems quickly.`,
    name: 'This will be used to identify the saved PagerDuty configuration.',
    token: 'This is your API token that will be used to send alerts to PagerDuty.',
    integration_key: 'This key can be found on your PagerDuty dashboard.',
    severities: 'Severities dictate which alerts will be sent to PagerDuty.',
    channelNamePlaceholder: 'pagerduty-main',
    apiTokenPlaceholder: 'YOUR API TOKEN HERE',
    integrationKeyPlaceholder: 'YOUR INTEGRATION KEY HERE',
  },
  opsGenie: {
    description: `Opsgenie is a modern incident management platform for operating 
      always-on services, empowering Dev and Ops teams to plan for service 
      disruptions and stay in control during incidents.`,
    name: 'This will be used to identify the saved OpsGenie configuration.',
    token: 'This is your API token that will be used to send alerts to OpsGenie.',
    eu: 'If you are operating OpsGenie in the EU region please have this ticked.',
    severities: 'Severities dictate which alerts will be sent to OpsGenie.',
    channelNamePlaceholder: 'opsgenie_main',
    apiTokenPlaceholder: 'YOUR API TOKEN HERE',
  },
};
