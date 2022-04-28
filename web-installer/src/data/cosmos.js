import {
  CHAINS_PAGE,
  CHANNELS_STEP,
  NODES_STEP,
  REPOSITORIES_STEP,
  CHAINS_STEP,
  ALERTS_STEP,
  DOCKER_STEP,
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
    sdkTip: `This endpoint is used to obtain validator metrics using Cosmos-Rest, namely jailed and bond statuses.
      When possible, the data retrieval is done indirectly by means of a non-validator as data source.
      However, the endpoint is ultimately required to determine whether the validator is reachable.
      Apart from this, firewall rules can be set up to only allow PANIC to access this endpoint. 
      Should this not be wanted, this endpoint can be safely disabled, however none of the mentioned
      validator metrics will be obtained.`,
    prometheusHolder: 'http://IP:26660/metrics',
    prometheusTip: `This IP address will be used to monitor prometheus based
      statistics, if omitted they will not be monitored and alerted on.`,
    exporterUrlHolder: 'http://IP:9100/metrics',
    exporterUrlTip: `This IP address will be used to monitor node exporter
      statistics, if omitted they will not be monitored and alerted on.`,
    isValidatorTip: 'Set True if the node you are setting up is a validator.',
    isArchiveTip: 'Set True if the node you are setting up is an archive node.',
    monitorNetworkTip: 'Set True if you want the blockchain monitor for data such as governance proposals.',
    monitorNodeTip: 'Set True if you want to monitor this configured node.',
    useAsDataSourceTip: 'Set True if you want to retrieve blockchain data from this node.',
    governanceAddressesHolder: 'cosmos1xn6ccr931loajcpg2rl0wue8jhwe8956ctvrae [Press Enter after each address].',
    operatorAddressHolder: 'cosmosvaloper124maqmcqv8tquy764ktz7cu0gxnzfw54n3vww8',
    operatorAddressTip: 'This is the validator address of the node you are monitoring.',
    backStep: CHAINS_STEP,
    nextStep: REPOSITORIES_STEP,
    tendermintRpcHolder: 'http://nodeip:26657',
    tendermintRpcTip: `This IP address will be used to obtain metrics from the
    Tendermint endpoint. If ommitted they wil not be monitored and alerted on`,
  },
  monitorNodesForm: {
    description: `Do you want to retrieve network metrics for <chain_name>?
    Setting this to True will enable monitoring data such as governance proposals.`,
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
    nextStep: DOCKER_STEP,
  },
  dockerHubForm: {
    title: 'DockerHub Repositories Setup',
    description: `You will now add a DockerHub repository that you want monitored
      and alerted on. You will receive informational alerts
      whenever there is a new release for the monitored repo. The default
      monitoring period for the DockerHub API is 1 hour.`,
    nameHolder: 'simplyvc/panic',
    nameTip: `The input should be in the form {repo-namespace}/{repo-name}, where
      repo-namespace is normally the username which owns the repo. In the case that
      a repo-namespace is not given, the input will be defaulted to library/{repo-name}.
      For example entering 'panic' will default to library/panic.`,
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
    backStep: DOCKER_STEP,
    nextStep: ALERTS_STEP,
  },
};
