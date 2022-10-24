import { MoreInfoType } from "../panic-installer-more-info-modal/panic-installer-more-info-modal";

export const CONTRACT_MORE_INFO: MoreInfoType[] = [
    {
        title: 'Basics',
        messages: [
        `Here we will confirm the network the Chainlink nodes are running on as well as test the weiwatchers url, which is used to pull a list of price feeds per network.
            The Chainlink and EVM nodes you have set up previously will be used as data sources to identify your node operator address and then ensure valid price feed participation.`
        ]
    },
    {
        title: 'Tips',
        messages: [
            `If the network you are looking for is not on the list then unfortunately there is no current price feed monitoring for that network.
            In this case you may add a custom url.
            However, you may experience unexpected behaviour due to the fact that your custom url is not tested by us, therefore make use of this feature at your own discretion.`
        ]
    }
];

export const HEADLINE: string = "Here you will configure the contracts you want monitored and triggering alerts";