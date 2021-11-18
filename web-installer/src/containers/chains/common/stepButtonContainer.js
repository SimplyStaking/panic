import React, { Component } from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { changeStep } from 'redux/actions/pageActions';
import NavigationButton from 'components/global/navigationButton';
import PopUp from 'components/global/popUp';

class StepButtonContainer extends Component {
  constructor(props) {
    super(props);
    this.nextStep = this.nextStep.bind(this);
    this.handlePopUpResponse = this.handlePopUpResponse.bind(this);
    this.state = {
      popUpActive: false,
      nextStep: '',
    };
  }

  handlePopUpResponse(bool) {
    const { stepChanger } = this.props;
    const { nextStep } = this.state;

    this.controlPopUpActivity(false);
    if (bool) {
      stepChanger({ step: nextStep });
    }
  }

  controlPopUpActivity(bool) {
    this.setState({
      popUpActive: bool,
    });
  }

  nextStep(step) {
    const { stepChanger, dirty } = this.props;

    if (!dirty) {
      // Change the upcoming page information
      stepChanger({ step });
    }

    this.setState({
      nextStep: step,
    });

    this.controlPopUpActivity(true);
  }

  render() {
    const { text, navigation, disabled } = this.props;
    const { popUpActive } = this.state;

    return (
      <>
        <NavigationButton
          disabled={disabled}
          nextPage={this.nextStep}
          buttonText={text}
          navigation={navigation}
        />
        <PopUp
          trigger={popUpActive}
          stepControlAdvanceNextStep={this.handlePopUpResponse}
        />
      </>
    );
  }
}

const mapStateToProps = (state) => ({
  step: state.ChangeStepReducer.step,
  dirty: state.ChangeStepReducer.dirty,
});

function mapDispatchToProps(dispatch) {
  return {
    stepChanger: (step) => dispatch(changeStep(step)),
  };
}

StepButtonContainer.propTypes = {
  disabled: PropTypes.bool.isRequired,
  stepChanger: PropTypes.func.isRequired,
  dirty: PropTypes.bool.isRequired,
  text: PropTypes.string.isRequired,
  navigation: PropTypes.string.isRequired,
};

export default connect(
  mapStateToProps,
  mapDispatchToProps,
)(StepButtonContainer);
