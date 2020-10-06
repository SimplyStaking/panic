import React, { Component } from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { changeStep } from '../../redux/actions/pageActions';
import NavigationButton from '../../components/global/navigationButton';

class StepButtonContainer extends Component {
  constructor(props) {
    super(props);
    this.nextStep = this.nextStep.bind(this);
  }

  nextStep(step) {
    const { stepChanger } = this.props;
    // Change the upcoming page information
    stepChanger({ step });
  }

  render() {
    const { text, navigation, disabled } = this.props;

    return (
      <NavigationButton
        disabled={disabled}
        nextPage={this.nextStep}
        buttonText={text}
        navigation={navigation}
      />
    );
  }
}

const mapStateToProps = (state) => ({
  step: state.ChangeStepReducer.step,
});

function mapDispatchToProps(dispatch) {
  return {
    stepChanger: (step) => dispatch(changeStep(step)),
  };
}

StepButtonContainer.propTypes = {
  disabled: PropTypes.bool.isRequired,
  stepChanger: PropTypes.func.isRequired,
  text: PropTypes.string.isRequired,
  navigation: PropTypes.string.isRequired,
};

export default connect(mapStateToProps, mapDispatchToProps)(StepButtonContainer);
