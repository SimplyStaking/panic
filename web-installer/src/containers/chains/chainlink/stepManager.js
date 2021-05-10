import React from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { AlertsChainlinkTableContainer } from 'containers/chains/common/alertsContainer';
import { ChainlinkChainFormContainer } from 'containers/chains/common/chainContainer';
import { ChannelsChainlinkTableContainer } from 'containers/chains/common/channelsContainer';
import {
  RepositoriesChainlinkFormContainer,
  RepositoriesChainlinkTableContainer,
} from 'containers/chains/common/repositoriesContainer';
import {
  DockerChainlinkFormContainer,
  DockerChainlinkTableContainer,
} from 'containers/chains/common/dockerContainer';
import {
  ALERTS_STEP,
  CHAINS_STEP,
  CHANNELS_STEP,
  NODES_STEP,
  REPOSITORIES_STEP,
  DOCKER_STEP,
} from 'constants/constants';
import { NodesFormContainer, NodesTableContainer } from './nodesContainer';
import { SystemChainlinkFormContainer, SystemChainlinkTableContainer } from '../common/systemsContainer';

const mapStateToProps = (state) => ({
  step: state.ChangeStepReducer.step,
});

// Returns the specific page according to pre-set steps
function getStep(stepName) {
  switch (stepName) {
    case ALERTS_STEP:
      return <AlertsChainlinkTableContainer />;
    case CHAINS_STEP:
      return <ChainlinkChainFormContainer />;
    case CHANNELS_STEP:
      return <ChannelsChainlinkTableContainer />;
    case NODES_STEP:
      return (
        <div>
          <NodesFormContainer />
          <NodesTableContainer />
          <SystemChainlinkFormContainer />
          <SystemChainlinkTableContainer />
        </div>
      );
    case REPOSITORIES_STEP:
      return (
        <div>
          <RepositoriesChainlinkFormContainer />
          <RepositoriesChainlinkTableContainer />
        </div>
      );
    case DOCKER_STEP:
      return (
        <div>
          <DockerChainlinkFormContainer />
          <DockerChainlinkTableContainer />
        </div>
      );
    default:
      return <ChainlinkChainFormContainer />;
  }
}

// Step Selector changes according to the step set
function StepManager(props) {
  const { step } = props;
  return <div>{getStep(step)}</div>;
}

StepManager.propTypes = {
  step: PropTypes.string.isRequired,
};

export default connect(mapStateToProps)(StepManager);
