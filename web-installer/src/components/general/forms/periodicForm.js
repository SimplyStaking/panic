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
    errors,
    values,
    handleSubmit,
    handleChange,
    setFieldValue,
  } = props;

  return (
    <div>
      <form onSubmit={handleSubmit} className={classes.root}>
        <Grid container spacing={3} justify="center" alignItems="center">
          <Grid item xs={2}>
            <Typography> Interval Seconds: </Typography>
          </Grid>
          <Grid item xs={10}>
            <TextField
              error={!errors.time !== true}
              value={values.time}
              type="text"
              name="time"
              placeholder="0"
              helperText={errors.time ? errors.time : ''}
              onChange={handleChange}
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
                    setFieldValue('enabled', !values.enabled);
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
  errors: PropTypes.shape({
    time: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    time: PropTypes.string.isRequired,
    enabled: PropTypes.bool.isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
  setFieldValue: PropTypes.func.isRequired,
};

export default PeriodicForm;
