import {
  CHAINS_PAGE,
  CHANNELS_STEP,
  NODES_STEP,
  REPOSITORIES_STEP,
  CHAINS_STEP,
  ALERTS_STEP,
  // DOCKER_STEP,
} from 'constants/constants';

export default {
  cosmos: {
    title: 'Cosmos-based Chain Setup',
  },
  chainForm: {
    title: 'Chain Name',
    description: `We will now go through the setup process of a Cosmos-based 
      chain. Firstly, you will enter the unique identifier of this chain. 
      The unique identifier is the name of the chain the nodes to be monitored 
      belong to. It should infer the types of nodes you will be 
      monitoring. For example, do not set-up Kava nodes under the Akash chain, 
      but set-up a chain for Kava and a chain for Akash and add the respective 
      nodes underneath them.`,
    placeholder: 'cosmos',
    tooltip: 'This will be used to identify the current chain that you are setting up.',
    backStep: CHAINS_PAGE,
    nextStep: NODES_STEP,
  },
  nodeForm: {
    title: 'Cosmos Node Setup',
    description: `This is the node's setup step, here you will configure the 
      nodes you want monitored and alerted on. For each node you 
      will enter a unique identifier so as a user you will know 
      which node is being alerted on. A suggestion would be to add 
      the IP Address to the node name e.g 
      cosmos_main_validator(IP) so that you will know 
      straight away where to look for the node. Do not use [] in your 
      names as you will not be able to load the configuration. If you want 
      the system which your node is running on to be monitored for 
      system metrics such as RAM and CPU usage please install 
      Node Exporter on it.`,
    nameHolder: 'cosmos_node_1(IP)',
    nameTip: 'This unique identifier will be used to identify your node.',
    tendermintHolder: 'http://IP:26657',
    tendermintTip: `This IP address will be used to monitor tendermint based 
      statistics, if omitted they will not be monitored and alerted on.`,
    sdkHolder: 'http://IP:1317',
    sdkTip: `This IP address will be used to monitor cosmos SDK based 
      statistics, if omitted they will not be monitored and alerted on.`,
    prometheusHolder: 'http://IP:26660/metrics',
    prometheusTip: `This IP address will be used to monitor prometheus based 
      statistics, if omitted they will not be monitored and alerted on.`,
    exporterUrlHolder: 'http://IP:9100/metrics',
    exporterUrlTip: `This IP address will be used to monitor node exporter 
      statistics, if omitted they will not be monitored and alerted on.`,
    isValidatorTip: 'Set True if the node you are setting up is a validator.',
    isArchiveTip: 'Set True if the node you are setting up is an archive node.',
    monitorNodeTip: 'Set True if you want to monitor this configured node.',
    useAsDataSourceTip: 'Set True if you want to retrieve blockchain data from this node.',
    backStep: CHAINS_STEP,
    nextStep: REPOSITORIES_STEP,
  },
  repoForm: {
    title: 'Github Repositories Setup',
    description: `You will now add a github repository that you want monitored 
      and alerted on. You will receive informational alerts 
      whenever there is a new release for the monitored repo. 
      You must enter the path of the repository with a trailing 
      forward slash, so if you want to monitor 
      https://github.com/tendermint/tendermint/ you will need to 
      enter tendermint/tendermint/ into the field below. The default 
      monitoring period of the GitHub API is 1 hour.`,
    nameHolder: 'tendermint/tendermint/',
    nameTip: `This is the path of the repository that will be monitored. E.g: 
      If the full URL is https://github.com/tendermint/tendermint/ then you 
      have to enter tendermint/tendermint/.`,
    monitorTip: 'Set True if you want to monitor this repository.',
    backStep: NODES_STEP,
    nextStep: CHANNELS_STEP,
  },
  dockerHubForm: {
    title: 'DockerHub Repositories Setup',
    description: `You will now add a DockerHub repository that you want monitored 
      and alerted on. You will receive informational alerts 
      whenever there is a new release for the monitored repo. The default 
      monitoring period for the DockerHub API is 1 hour.`,
    nameHolder: 'simplyvc/panic',
    nameTip: `This is the path of the repository that will be monitored. E.g: 
      If the full URL is https://hub.docker.com/r/simplyvc/panic 
      then you have to enter simplyvc/panic .`,
    monitorTip: 'Set True if you want to monitor this repository.',
    backStep: REPOSITORIES_STEP,
    nextStep: CHANNELS_STEP,
  },

  channelsTable: {
    title: 'Choose Alerting Channels',
    description: `Select the alert channels that will be used for the added network. 
      For the same chain, you can select as many channel configurations from as many 
      channels as you want.`,
    empty: "You haven't setup any channels! You will not be alerted on this chain!",
    backStep: CHANNELS_STEP,
    nextStep: ALERTS_STEP,
  },
};
