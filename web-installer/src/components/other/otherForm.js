import React from 'react';
import PropTypes from 'prop-types';
import {
  TextField, Typography, Grid,
} from '@material-ui/core';
import { makeStyles } from '@material-ui/core/styles';

const useStyles = makeStyles(() => ({
  root: {
    display: 'flex',
    flexWrap: 'wrap',
    width: '100%',
  },
}));

const OtherForm = (props) => {
  const classes = useStyles();

  const {
    errors,
    handleSubmit,
    handleChange,
    values,
  } = props;

  return (
    <div>
      <form onChange={handleSubmit} className={classes.root}>
        <Grid container spacing={3} justify="center" alignItems="center">
          <Grid item xs={2}>
            <Typography> Periodic Alive Reminder: </Typography>
          </Grid>
          <Grid item xs={10}>
            <TextField
              error={!errors.periodic !== true}
              value={values.periodic}
              type="text"
              name="periodic"
              placeholder="86400"
              helperText={errors.periodic ? errors.periodic : ''}
              onChange={handleChange}
              fullWidth
            />
          </Grid>
        </Grid>
      </form>
    </div>
  );
};

OtherForm.propTypes = {
  errors: PropTypes.shape({
    periodic: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    periodic: PropTypes.string.isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
};

export default OtherForm;
