import React from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import AlertsContainer from './alertsContainer';
import ChainContainer from './chainContainer';
import ChannelsContainer from './channelsContainer';
import { KMSFormContainer, KMSTableContainer } from './kmsContainer';
import { NodesFormContainer, NodesTableContainer } from './nodesContainer';
import { RepositoriesFormContainer, RepositoriesTableContainer } from './repositoriesContainer';

import {
  ALERTS_STEP, CHAINS_STEP, CHANNELS_STEP, KMS_STEP, NODES_STEP,
  REPOSITORIES_STEP,
} from '../../../constants/constants';

const mapStateToProps = (state) => ({ step: state.ChangeStepReducer.step });

// Returns the specific page according to pre-set steps
function getStep(stepName) {
  switch (stepName) {
    case ALERTS_STEP:
      return <AlertsContainer />;
    case CHAINS_STEP:
      return <ChainContainer />;
    case CHANNELS_STEP:
      return <ChannelsContainer />;
    case KMS_STEP:
      return (
        <div>
          <KMSFormContainer />
          <KMSTableContainer />
        </div>
      );
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
      return <ChainContainer />;
  }
}

// Step Selector changes according to the step set
function StepManger(props) {
  const { step } = props;
  return (
    <div>
      {getStep(step)}
    </div>
  );
}

StepManger.propTypes = {
  step: PropTypes.string.isRequired,
};

export default connect(mapStateToProps)(StepManger);
