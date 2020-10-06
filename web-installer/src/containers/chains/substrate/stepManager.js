import React from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import AlertsContainer from './alertsContainer';
import { SubstrateChainFormContainer } from '../general/chainContainer';
import ChannelsContainer from './channelsContainer';
import { NodesFormContainer, NodesTableContainer } from './nodesContainer';
import { RepositoriesFormContainer, RepositoriesTableContainer } from './repositoriesContainer';

import {
  ALERTS_STEP, CHAINS_STEP, CHANNELS_STEP, NODES_STEP,
  REPOSITORIES_STEP,
} from '../../../constants/constants';

const mapStateToProps = (state) => ({
  step: state.ChangeStepReducer.step,
});

// Returns the specific page according to pre-set steps
function getStep(stepName) {
  switch (stepName) {
    case ALERTS_STEP:
      return <AlertsContainer />;
    case CHAINS_STEP:
      return <SubstrateChainFormContainer />;
    case CHANNELS_STEP:
      return <ChannelsContainer />;
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
          <RepositoriesFormContainer />
          <RepositoriesTableContainer />
        </div>
      );
    default:
      return <SubstrateChainFormContainer />;
  }
}

// Step Selector changes according to the step set
function StepManager(props) {
  const { step } = props;
  return (
    <div>
      {getStep(step)}
    </div>
  );
}

StepManager.propTypes = {
  step: PropTypes.string.isRequired,
};

export default connect(mapStateToProps)(StepManager);
