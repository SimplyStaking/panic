import { MoreInfoType } from "../panic-installer-more-info-modal/panic-installer-more-info-modal";

export const EVM_NODE_MORE_INFO: MoreInfoType[] = [
    {
      title: 'Basics',
      messages: [
        ` 
          Here you will configure EVM nodes you want to be monitored and alerted on.
          You are able to setup any nodes as long as they are compatible with the standard Ethereum JSON RPC, for example Ethereum, Matic, Binance Smart Chain, etc.
        `
      ]
    },
    {
      title: 'Tips',
      messages: [
        `For each node you will enter a unique identifier so as a user you will know which node is being alerted on.
            An example of an EVM node name is suggested to be ethereum_node.
            These nodes will be used to retrieve Ethereum network and Chainlink contract data, to give visibility into price feed rounds.
            The default monitoring period of the RPC data source is 10 seconds.
        `
      ]
    }
];

export const EVM_NODE_HEADLINE = "Here you will configure EVM nodes you want to be monitored and alerted on.";