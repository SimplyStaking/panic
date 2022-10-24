export const CHANNEL_TABLE_HEADERS = [
  {
    title: "Channel Type",
    sortable: true
  },
  {
    title: "Name",
    sortable: true
  },
  {
    title: "Enabled",
    sortable: true
  }
];
export const MORE_INFO_MESSAGES = [
  {
    title: "What Are Channels?",
    messages: [
      "Channels allow for different modes of communication such as directly calling your phone, or sending messages on Telegram.",
      "Channels such as Telegram allow for commands to be inputted. This enables user interaction with the alerter."
    ]
  },
  {
    title: "Supported Channels",
    messages: [
      "Telegram: a cross-platform cloud-based instant messaging, video calling, and VoIP service.",
      `Twilio: allows software developers to programmatically make and receive phone calls.`,
      "PagerDuty: a SaaS incident response platform for IT departments.",
      `OpsGenie: an advanced incident response orchestration platform for DevOps and IT Teams.`,
      "Email: this can either be a private email server or one provided by a company such as Google."
    ]
  },
  {
    title: "How are they setup?",
    messages: [
      "Channels are set up in the current section and you may add as many channels as you want.",
      "Each channel can be used across different sub-chains. For example, one specific Telegram bot can be used for a sub-chain configured under Cosmos and other one under Substrate base chain.",
      "For each channel, you have the option to select different alert severity levels. These selections will indicate which alerts the channel is going to receive."
    ]
  }
]

export const MAIN_TEXT = `Channels are used by PANIC to communicate with it's users.`
export const getSecondaryText = (chain_name: string) => {
  return `The channels added now under this sub-chain will be 
  available for future configurations, meaning that you can reuse channels across different sub-chains setups. 
  Tick the 'Enabled' checkbox to enable PANIC alerting for the ${chain_name} chain via that channel.`
}
