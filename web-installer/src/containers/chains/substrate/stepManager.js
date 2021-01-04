import React from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { AlertsSubstrateTableContainer } from 'containers/chains/common/alertsContainer';
import { SubstrateChainFormContainer } from 'containers/chains/common/chainContainer';
import { ChannelsSubstrateTableContainer } from 'containers/chains/common/channelsContainer';
import {
  RepositoriesSubstrateFormContainer,
  RepositoriesSubstrateTableContainer,
} from 'containers/chains/common/repositoriesContainer';
import {
  ALERTS_STEP,
  CHAINS_STEP,
  CHANNELS_STEP,
  NODES_STEP,
  REPOSITORIES_STEP,
} from 'constants/constants';
import { NodesFormContainer, NodesTableContainer } from './nodesContainer';

const mapStateToProps = (state) => ({
  step: state.ChangeStepReducer.step,
});

// Returns the specific page according to pre-set steps
function getStep(stepName) {
  switch (stepName) {
    case ALERTS_STEP:
      return <AlertsSubstrateTableContainer />;
    case CHAINS_STEP:
      return <SubstrateChainFormContainer />;
    case CHANNELS_STEP:
      return <ChannelsSubstrateTableContainer />;
    case NODES_STEP:
      return (
        <div>
          <NodesFormContainer />
          <NodesTableContainer />
        </div>
      );
    case REPOSITORIES_STEP:
      return (
        <div>
          <RepositoriesSubstrateFormContainer />
          <RepositoriesSubstrateTableContainer />
        </div>
      );
    default:
      return <SubstrateChainFormContainer />;
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
