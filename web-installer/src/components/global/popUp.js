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

          <Grid container item xs={4} justify="center">
            <WarningIcon fontSize="large" />
          </Grid>
          <Typography variant="h5">
            Continuing will reset the unsubmitted data in this form.
          </Typography>
          <Typography variant="h6">
            Are you sure you would like to proceed?
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
            Hint: Press ADD NODE when node details have been filled.
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
