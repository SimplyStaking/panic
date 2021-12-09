import React from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { AlertsGeneralTableContainer } from 'containers/chains/common/alertsContainer';
import { ChannelsGeneralTableContainer } from 'containers/chains/common/channelsContainer';
import {
  SystemGeneralFormContainer,
  SystemGeneralTableContainer,
} from 'containers/chains/common/systemsContainer';
import {
  RepositoriesGeneralFormContainer,
  RepositoriesGeneralTableContainer,
} from 'containers/chains/common/repositoriesContainer';
// import {
// DockerHubGeneralFormContainer,
// DockerHubGeneralTableContainer,
// } from 'containers/chains/common/dockerHubContainer';
import {
  ALERTS_STEP,
  CHANNELS_STEP,
  REPOSITORIES_STEP,
  SYSTEMS_STEP,
  // DOCKER_STEP,
} from 'constants/constants';

const mapStateToProps = (state) => ({
  step: state.ChangeStepReducer.step,
});

// Returns the specific page according to pre-set steps
function getStep(stepName) {
  switch (stepName) {
    case ALERTS_STEP:
      return <AlertsGeneralTableContainer />;
    case CHANNELS_STEP:
      return <ChannelsGeneralTableContainer />;
    case SYSTEMS_STEP:
      return (
        <div>
          <SystemGeneralFormContainer />
          <SystemGeneralTableContainer />
        </div>
      );
    case REPOSITORIES_STEP:
      return (
        <div>
          <RepositoriesGeneralFormContainer />
          <RepositoriesGeneralTableContainer />
        </div>
      );
    // case DOCKER_STEP:
    //   return (
    //     <div>
    //       <DockerHubGeneralFormContainer />
    //       <DockerHubGeneralTableContainer />
    //     </div>
    //   );
    default:
      return (
        <div>
          <SystemGeneralFormContainer />
          <SystemGeneralTableContainer />
        </div>
      );
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
