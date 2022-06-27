import React from 'react';
import Button from 'components/material_ui/CustomButtons/Button';
import ErrorIcon from '@material-ui/icons/Error';
import CheckCircleIcon from '@material-ui/icons/CheckCircle';
import PlayArrowIcon from '@material-ui/icons/PlayArrow';
import { ToastsStore } from 'react-toasts';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';

// generic button component that takes a ping method depending on the
//  type of ping required, and dynamically changes colour/icon depending on
//  whether the connection was successful or not.
class TestButtonWithStatus extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      connection: 0,
    };
  }

  getButtonDesignData() {
    const { connection } = this.state;

    let colour;
    let icon;

    if (connection === 1) {
      colour = 'success';
      icon = <CheckCircleIcon />;
    } else if (connection === 0) {
      colour = 'primary';
      icon = <PlayArrowIcon />;
    } else {
      colour = 'danger';
      icon = <ErrorIcon />;
    }

    return [colour, icon];
  }

  async SendPing() {
    const { url, metric, pingMethod } = this.props;
    let connectionState = 0;
    try {
      ToastsStore.info(`Connecting with URL ${url}`, 5000);
      await pingMethod(url, metric);
      ToastsStore.success('Successfully connected', 5000);
      connectionState = 1;
    } catch (e) {
      if (e.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        ToastsStore.error(
          `Could not connect with URL ${url}. Error: ${e.response.data.message}`,
          5000,
        );
      } else {
        // Something happened in setting up the request that triggered an Error
        ToastsStore.error(
          `Could not connect with URL ${url}. Error: ${e.message}`,
          5000,
        );
      }
      connectionState = -1;
    }

    this.setState({
      connection: connectionState,
    });
  }

  render() {
    const { disabled } = this.props;

    const buttonDesignData = this.getButtonDesignData();
    const colour = buttonDesignData[0];
    const icon = buttonDesignData[1];

    return (
      <Button
        color={colour}
        size="md"
        disabled={disabled}
        onClick={() => {
          this.SendPing();
        }}
        endIcon={icon}
      >
        Test
      </Button>
    );
  }
}

TestButtonWithStatus.propTypes = forbidExtraProps({
  disabled: PropTypes.bool.isRequired,
  url: PropTypes.string.isRequired,
  pingMethod: PropTypes.func.isRequired,
  metric: PropTypes.string.isRequired,
});

export default TestButtonWithStatus;
