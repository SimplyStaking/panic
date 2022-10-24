import { MoreInfoType } from "../panic-installer-more-info-modal/panic-installer-more-info-modal";

export function getNodeMoreInfoByBaseChain(baseChainName: string): MoreInfoType[] {
    const moreInfo: MoreInfoType[] = [
        {
            title: 'Basics',
            messages: []
        },
        {
            title: 'Tips',
            messages: []
        }
    ];

    switch (baseChainName) {
        case "chainlink":
            moreInfo[0].messages = [
                `
                    Here you will configure the nodes you want to be monitored and alerted on, giving each node a unique identifier.
                    For example, chainlink_eth_ocr, which would specify the network and node type.
                `
            ];
            moreInfo[1].messages = [
                `
                    When running Chainlink nodes, a node operator may have multiple backup nodes, this means that those nodes also need to be monitored.
                `,
                `
                    Therefore under one configuration, the user must set up multiple Prometheus URLs for nodes.
                    The default monitoring interval of Prometheus polling is 10 seconds.
                `
            ];
        break;
        
        case "cosmos":
            moreInfo[0].messages = [
                `This is the node's setup step, here you will configure the nodes you want to be monitored and alerted on. For each node you will enter a unique identifier so as a user you will know which node is being alerted on. 
                If you want the system which your node is running on to be monitored for system metrics such as RAM and CPU usage please install Node Exporter on it.`
            ];
            moreInfo[1].messages = [
                `A suggestion would be to add the IP Address to the node name e.g cosmos_main_validator(IP) so that you will know straight away where to look for the node.`
            ];
        break;

        case "substrate":
            moreInfo[0].messages = [
                `This is the node's setup step, here you will configure the nodes you want to be monitored and alerted on. For each node you will enter a unique identifier so as a user you will know which node is being alerted on. 
                If you want the system which your node is running on to be monitored for system metrics such as RAM and CPU usage please install Node Exporter on it.`
            ];
            moreInfo[1].messages = [
                `A suggestion would be to add the IP Address to the node name e.g polkadot_main_validator(IP) so that you will know straight away where to look for the node.`
            ];
        break;
    }

    return moreInfo;
}

export const NODE_HEADLINE = "Here you will configure the nodes you want monitored and triggering alerts.";