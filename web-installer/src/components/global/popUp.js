import { Button, Grid, Typography } from '@material-ui/core';
import WarningIcon from '@material-ui/icons/Warning';
import React from 'react';
import PropTypes from 'prop-types';

const PopUp = (props) => {
  const { trigger, stepControlAdvanceNextStep } = props;
  return (trigger) ? (
    <div className="popup">
      <div className="popup-inner">

        <Grid container spacing={2} justifyContent="center" alignItems="center">

          <Grid container item xs={12} justify="center">
            <WarningIcon fontSize="large" />
          </Grid>
          <Typography variant="h5">
            Unsaved Changes.
          </Typography>
          <Typography variant="h6">
            Form contains changes that will be lost. Do you wish to proceed?
          </Typography>

          <Grid item xs={12} />

          <Button
            style={{ width: '100px', margin: '10px' }}
            size="medium"
            variant="contained"
            onClick={() => stepControlAdvanceNextStep(false)}
          >
            Stay
          </Button>
          <Button
            style={{ width: '100px', margin: '10px' }}
            size="medium"
            variant="contained"
            onClick={() => stepControlAdvanceNextStep(true)}
          >
            Continue
          </Button>
          <Grid item xs={12} />
          <Typography variant="h7">
            Hint: Be sure to press ADD after filling in the form details.
          </Typography>
        </Grid>
      </div>
    </div>
  ) : '';
};

PopUp.propTypes = {
  trigger: PropTypes.bool.isRequired,
  stepControlAdvanceNextStep: PropTypes.func.isRequired,
};

export default PopUp;
