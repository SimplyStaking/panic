import {
  CHAINS_PAGE,
  CHANNELS_STEP,
  NODES_STEP,
  CHAINS_STEP,
  REPOSITORIES_STEP,
  ALERTS_STEP,
  DOCKER_STEP,
} from 'constants/constants';

export default {
  substrate: {
    title: 'Substrate-based Chain Setup',
  },
  chainForm: {
    title: 'Chain Name Setup',
    description: `We will now go through the setup process of a Substrate based
      chain. Firstly, you will enter the unique identifier of this chain.
      The unique identifier is the name of the chain the nodes to be monitored
      belong to. It should infer the types of nodes you will be
      monitoring. If you are going to be monitoring Polkadot nodes
      then the identifier should be Polkadot and you shouldn't
      add nodes which do not belong to the Polkadot blockchain. For
      example, do not setup Moonbeam nodes under the Polkadot chain
      but setup a chain for Moonbeam and a chain for Polkadot, and
      add respective nodes underneath them.`,
    placeholder: 'polkadot',
    tooltip: 'This will be used to identify the current chain that you are setting up.',
    backStep: CHAINS_PAGE,
    nextStep: NODES_STEP,
  },
  nodeForm: {
    title: 'Nodes Setup',
    description: `This is the node's setup step, here you will configure the
      nodes you want monitored and alerted on. For each node you
      will enter a unique identifier so as a user you will know
      which node is being alerted on. A suggestion would be to add
      the IP Address to the node name e.g
      polkadot_main_validator(IP) so that you will know
      straight away where to look for the node. Do not use [] in your
      names as you will not be able to load the configuration. If you want
      the system which your node is running on to be monitored for
      system metrics such as RAM and CPU usage, please install
      Node Exporter on it.`,
    nameHolder: 'polkadot_node_1(IP)',
    nameTip: 'This unique identifier will be used to identify your node.',
    websocketHolder: 'ws://IP:9944',
    websocketTip: `This IP address will be used to monitor the polkadot node
      statistics, if omitted they will not be monitored and alerted on.`,
    exporterUrlHolder: 'http://IP:9100/metrics',
    exporterUrlTip: `This IP address will be used to monitor node exporter
      statistics, if omitted they will not be monitored and alerted on.`,
    stashAddressHolder: 'EDDJBTFGdsg0gh8sd0sdsda2asd12dasdafs',
    stashAddressTip: 'This will be used to monitor the stash address account.',
    governanceAddressHolder: '12xtGHlkyrmbniiWQqJtECiBQrMn8AypQcXhnQAc6RB6JlKm [Press Enter after each address]',
    governanceAddressTip:
      'The address which you are voting in governance with and want monitored.',
    isValidatorTip: 'Set True if the node you are setting up is a validator.',
    isArchiveTip: 'Set True if the node you are setting up is an archive node.',
    monitorNodeTip: 'Set True if you want to monitor this configured node.',
    useAsDataSourceTip: 'Set True if you want to retrieve blockchain data from this node.',
    backStep: CHAINS_STEP,
    nextStep: REPOSITORIES_STEP,
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
      https://github.com/paritytech/substrate/ you will need to
      enter paritytech/substrate/ into the field below. The default
      monitoring period of the GitHub API is 1 hour.`,
    nameHolder: 'paritytech/substrate/',
    nameTip: `This is the path of the repository that will be monitored. E.g:
      If the full URL is https://github.com/paritytech/substrate/ then you
      have to enter paritytech/substrate/.`,
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
    description: `Choose to which channels, alerts belonging to the added chain should be forwarded to.
      For the same chain, you can select as many channel configurations from as many
      channels as you want.`,
    empty: "You haven't setup any channels! You will not be alerted on this chain!",
    backStep: REPOSITORIES_STEP,
    nextStep: ALERTS_STEP,
  },
};
