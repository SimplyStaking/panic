import {
  CHANNELS_STEP,
  NODES_STEP,
  REPOSITORIES_STEP,
  // DOCKER_STEP,
  ALERTS_STEP,
  CHAINS_PAGE,
} from 'constants/constants';

export default {
  general: {
    title: 'General Settings',
  },
  periodic: {
    title: 'Periodic Alive Reminder',
    description: `The periodic alive reminder is used to notify you that PANIC 
      and all of it's components are fully operational. If enabled 
      and configured you will receive INFO alerts every (n) 
      seconds notifying you that PANIC is operational. If the 
      interval is very small this will result in you getting 
      spammed with alerts, a suggestion is to keep it at a couple 
      of hours.`,
  },
  repoForm: {
    title: 'Github Repositories Setup',
    description: `You will now add a github repository that you want monitored 
      and alerted on. You will receive informational alerts 
      whenever there is a new release for the monitored repo. 
      You must enter the path of the repository with a trailing 
      forward slash, so if you want to monitor 
      https://github.com/SimplyVC/panic/ you will need to 
      enter SimplyVC/panic/ into the Field below. The default 
      monitoring period of the GitHub API is 1 hour.`,
    nameHolder: 'SimplyVC/panic/',
    nameTip: `This is the path of the repository that will be monitored. E.g: 
      If the full URL is https://github.com/SimplyVC/panic/ then you 
      have to enter SimplyVC/panic/.`,
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
  systemForm: {
    title: 'Systems Setup',
    description: `Here we will setup the monitoring of systems which do not 
      belong to any chain. These systems wouldn't have any 
      previously setup nodes running on them but you would still 
      want the system's metrics monitored. For example you can 
      monitor the system that is running PANIC! The System's metrics 
      are monitored through Node Exporter, so that will need to be 
      installed on each system you want to monitor. The default 
      monitoring period for system monitoring is 60 seconds.`,
    nameHolder: 'panic_system',
    nameTip: 'This will be used to identify the current System configuration.',
    monitorTip: 'Set True if you want to monitor this repository.',
    exporterUrlHolder: 'http://IP:9100/metrics',
    exporterUrl: 'This is the node exporter URL of your system.',
    monitorSystemTip: 'Set to True if you want your system monitored.',
    backStep: CHAINS_PAGE,
    nextStep: REPOSITORIES_STEP,
  },
  channelsTable: {
    title: 'Choose Alerting Channels',
    description: `Choose the channels which should receive alerts related to general repositories 
      and systems, and the periodic alive reminder You can select as many configurations 
      as you want from as many channels as you want.`,
    empty: "You haven't setup any channels! You will not be alerted on this chain!",
    backStep: REPOSITORIES_STEP,
    nextStep: ALERTS_STEP,
  },
};
