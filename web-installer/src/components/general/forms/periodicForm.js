import React from 'react';
import PropTypes from 'prop-types';
import {
  TextField, Typography, Grid, Switch, FormControlLabel,
} from '@material-ui/core';
import { makeStyles } from '@material-ui/core/styles';

const useStyles = makeStyles(() => ({
  root: {
    display: 'flex',
    flexWrap: 'wrap',
    width: '100%',
  },
}));

const PeriodicForm = (props) => {
  const classes = useStyles();

  const {
    values,
    periodic,
    savePeriodicDetails,
  } = props;

  return (
    <div>
      <form className={classes.root}>
        <Grid container spacing={3} justify="center" alignItems="center">
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

PeriodicForm.propTypes = {
  periodic: PropTypes.shape({
    time: PropTypes.string,
    enabled: PropTypes.bool,
  }).isRequired,
  values: PropTypes.shape({
    time: PropTypes.string,
    enabled: PropTypes.bool,
  }).isRequired,
  savePeriodicDetails: PropTypes.func.isRequired,
};

export default PeriodicForm;
