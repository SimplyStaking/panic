import { MoreInfoType } from "../panic-installer-more-info-modal/panic-installer-more-info-modal";

export function getSystemMoreInfoByBaseChain(baseChainName: string) {
    const moreInfo: MoreInfoType[] = [
        {
          title: 'Basics',
          messages: []
        },
        {
          title: 'Tips',
          messages: []
        }
    ]
    
      switch (baseChainName) {
        case "chainlink":
          moreInfo[0].messages = [
            "Here we will setup the monitoring of systems which Chainlink or EVM nodes are running on."
          ];
          moreInfo[1].messages = [
            "Node Exporter needs to be installed on each system you want monitored including those which run backup nodes.",
            "The default monitoring period for system monitoring is 60 seconds."
          ];
          break;
        case "general":
          moreInfo[0].messages = [
              `
                Here we will setup the monitoring of systems which do not belong to any chain.
                These systems wouldn't have any previously setup nodes running on them but you would still want the system's metrics monitored.
              `
          ];
          moreInfo[1].messages = [
            `
              For example you can monitor the system that is running PANIC!
              The System's metrics are monitored through Node Exporter, so that will need to be installed on each system you want to monitor.
            `,
            `
              The default monitoring period for system monitoring is 60 seconds.
            `
          ]
          break;
      }
    
      return moreInfo;
}

export const SYSTEM_HEADLINE = "Here we will setup the monitoring of systems which do not belong to any chain.";