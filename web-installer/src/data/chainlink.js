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
  chainlink: {
    title: 'Chainlink Network Setup',
  },
  chainForm: {
    title: 'Network Name Setup',
    description: `We will now go through the setup process of a network that Chainlink
      nodes are going to be connected to, together with the Chainlink nodes
      themselves. Firstly, you will enter the unique identifier of this network.
      The unique identifier is the name of the network the nodes to be
      monitored are connected to. For example, do not set-up Chainlink nodes
      that are connected to Ethereum under the name Binance Smart Chain.`,
    placeholder: 'ethereum',
    tooltip: 'This will be used to identify the current network that you are setting up.',
    backStep: CHAINS_PAGE,
    nextStep: NODES_STEP,
  },
  nodeForm: {
    title: 'Nodes Setup',
    description: `Here you will configure the nodes you want to be monitored and
      alerted on, giving each node a unique identifier. For example,
      chainlink_eth_ocr, which would specify the network and node type. When
      running Chainlink nodes, a node operator may have multiple backup nodes,
      this means that those nodes also need to be monitored. Therefore under one
      configuration, the user must set up multiple Prometheus URLs for nodes.
      The default monitoring interval of Prometheus polling is 10 seconds.`,
    nameHolder: 'chainlink_eth_ocr',
    nameTip: 'This unique identifier will be used to identify your node.',
    prometheusHolder: 'http://IP:6688/metrics [Press Enter after each URL].',
    prometheusTip:
      'This IP address will be used to monitor prometheus based '
      + 'metrics, if omitted they will not be monitored and alerted on.',
    exporterUrlHolder: 'http://IP:9100/metrics',
    exporterUrlTip:
      'This IP address will be used to monitor node exporter '
      + 'metrics, if omitted they will not be monitored and alerted on.',
    monitorNodeTip: 'Set True if you want to monitor this configured node.',
    backStep: CHAINS_STEP,
    nextStep: REPOSITORIES_STEP,
  },
  evmForm: {
    title: 'EVM Nodes Setup',
    description: `Here you will configure EVM nodes you want to be monitored and
      alerted on. You are able to setup any nodes as long as they are compatible
      with the standard Ethereum JSON RPC, for example Ethereum, Matic, Binance
      Smart Chain, etc. For each node you will enter a unique identifier so as
      a user you will know which node is being alerted on. An example of an
      EVM node name is suggested to be ethereum_node. These nodes will be used
      to retrieve Ethereum network and Chainlink contract data, to give
      visibility into price feed rounds. The default monitoring period
      of the RPC data source is 10 seconds.`,
    nameHolder: 'ethereum_main_node',
    nameTip: 'This unique identifier will be used to identify your node.',
    httpUrlHolder: 'http://IP:8545',
    httpUrlTip:
      'This IP address will be used to monitor prometheus based '
      + 'metrics, if omitted they will not be monitored and alerted on.',
    monitorNodeTip: 'Set True if you want to monitor this configured node.',
    backStep: CHAINS_STEP,
    nextStep: REPOSITORIES_STEP,
  },
  contractForm: {
    title: 'Contract Monitoring Setup',
    description: `Here we will confirm the network the Chainlink nodes are
    running on as well as test the weiwatchers url, which is used to pull a list
    of price feeds per network. The Chainlink and EVM nodes you have set up
    above will be used as data sources to identify your node operator address
    and then ensure valid price feed participation. If the network you are
    looking for is not on the list then unfortunately there is no current price
    feed monitoring for that network. In this case you may add a custom url.
    However, you may experience unexpected behaviour due to the fact that your
    custom url is not tested by us, therefore make use of this feature at your own discretion.`,
    nameHolder: 'ethereum',
    nameTip: 'The name of the network to be added to the drop-down list of networks.',
    urlTip: 'The URL of the network to be added to the drop-down list of networks.',
    weiWatchersUrlHolder: 'https://weiwatchers.com/feeds-mainnet.json',
    weiWatchersUrlTip: 'This is used to retrieve a list of price feeds for the specified network.',
    monitorContractTip: 'Set True if you want to monitor price feed contract for this chain.',
    backStep: CHAINS_STEP,
    nextStep: REPOSITORIES_STEP,
  },
  repoForm: {
    title: 'GitHub Repositories Setup',
    description: `You will now add a github repository that you want monitored
      and alerted on. You will receive informational alerts
      whenever there is a new release for the monitored repo.
      You must enter the path of the repository with a trailing
      forward slash, so if you want to monitor
      https://github.com/smartcontractkit/chainlink/ you will need to
      enter smartcontractkit/chainlink/ into the field below. The default
      monitoring period of the GitHub API is 1 hour.`,
    nameHolder: 'smartcontractkit/chainlink/',
    nameTip: `This is the path of the repository that will be monitored. E.g:
      If the full URL is https://github.com/smartcontractkit/chainlink/ then you
      have to enter smartcontractkit/chainlink/.`,
    monitorTip: 'Set True if you want to monitor this repository.',
    backStep: NODES_STEP,
    nextStep: DOCKER_STEP,
  },
  systemForm: {
    title: 'Systems Setup',
    description: `Here we will setup the monitoring of systems which Chainlink
    or EVM nodes are running on. Node Exporter needs to be installed on each
    system you want monitored including those which run backup nodes. The
    default monitoring period for system monitoring is 60 seconds.`,
    nameHolder: 'system_chainlink_eth_ocr',
    nameTip: 'This will be used to identify the current System configuration.',
    monitorTip: 'Set True if you want to monitor this repository.',
    exporterUrlHolder: 'http://IP:9100/metrics',
    exporterUrl: 'This is the node exporter URL of your system.',
    monitorSystemTip: 'Set to True if you want your system monitored.',
    backStep: CHAINS_STEP,
    nextStep: REPOSITORIES_STEP,
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
    description: `Choose to which channels, alerts belonging to the added chain should be forwarded to.
      For the same chain, you can select as many channel configurations from as many
      channels as you want.`,
    empty: "You haven't setup any channels! You will not be alerted on this chain!",
    backStep: REPOSITORIES_STEP,
    nextStep: ALERTS_STEP,
  },
};
