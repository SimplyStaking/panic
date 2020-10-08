import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import {
  TextField, Typography, Grid, Switch, FormControlLabel,
} from '@material-ui/core';
import { useStyles } from '../../theme/default';
import MainText from '../../global/mainText';

const PeriodicForm = (values, periodic, savePeriodicDetails) => {
  const classes = useStyles();

  return (
    <div>
      <MainText
        text="Preiodic alive reminder description"
      />
      <form className={classes.root}>
        <Grid container spacing={3} justify="center" alignItems="center">
          <Grid item xs={12} />
          <Grid item xs={2}>
            <Typography> Interval Seconds: </Typography>
          </Grid>
          <Grid item xs={10}>
            <TextField
              value={values.time}
              type="text"
              name="time"
              placeholder="0"
              onChange={(event) => {
                savePeriodicDetails({
                  time: event.target.value,
                  enabled: periodic.enabled,
                });
              }}
              fullWidth
            />
          </Grid>
          <Grid item xs={2}>
            <Typography> Enabled: </Typography>
          </Grid>
          <Grid item xs={1}>
            <FormControlLabel
              control={(
                <Switch
                  checked={values.enabled}
                  onClick={() => {
                    savePeriodicDetails({
                      time: periodic.time,
                      enabled: !periodic.enabled,
                    });
                  }}
                  name="enabled"
                  color="primary"
                />
              )}
            />
          </Grid>
          <Grid item xs={9} />
        </Grid>
      </form>
    </div>
  );
};

PeriodicForm.propTypes = forbidExtraProps({
  periodic: PropTypes.shape({
    time: PropTypes.string,
    enabled: PropTypes.bool,
  }).isRequired,
  values: PropTypes.shape({
    time: PropTypes.string,
    enabled: PropTypes.bool,
  }).isRequired,
  savePeriodicDetails: PropTypes.func.isRequired,
});

export default PeriodicForm;
