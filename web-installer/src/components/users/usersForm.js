import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import { TextField, Typography, Grid } from '@material-ui/core';
import { makeStyles } from '@material-ui/core/styles';
import { AddAccount } from '../../utils/buttons';

const useStyles = makeStyles(() => ({
  root: {
    display: 'flex',
    flexWrap: 'wrap',
    width: '100%',
  },
}));

const UsersForm = ({errors, values, handleSubmit, handleChange}) => {
  const classes = useStyles();

  return (
    <div>
      <form onSubmit={handleSubmit} className={classes.root}>
        <Grid container spacing={3} justify="center" alignItems="center">
          <Grid item xs={2}>
            <Typography> Username: </Typography>
          </Grid>
          <Grid item xs={10}>
            <TextField
              error={errors.username}
              value={values.username}
              type="text"
              name="username"
              placeholder="panic_user_main"
              helperText={errors.username ? errors.username : ''}
              onChange={handleChange}
              fullWidth
            />
          </Grid>
          <Grid item xs={2}>
            <Typography> Password: </Typography>
          </Grid>
          <Grid item xs={10}>
            <TextField
              error={errors.password}
              value={values.password}
              type="password"
              name="password"
              placeholder="*****************"
              helperText={errors.password ? errors.password : ''}
              onChange={handleChange}
              fullWidth
            />
          </Grid>
          <Grid item xs={8} />
          <Grid item xs={4}>
            <Grid container direction="row" justify="flex-end" alignItems="center">
              <AddAccount
                disabled={(Object.keys(errors).length !== 0)}
                username={values.username}
                password={values.password}
              />
            </Grid>
          </Grid>
        </Grid>
      </form>
    </div>
  );
};

UsersForm.propTypes = forbidExtraProps({
  errors: PropTypes.shape({
    username: PropTypes.string,
    password: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    username: PropTypes.string.isRequired,
    password: PropTypes.string.isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
});

export default UsersForm;
