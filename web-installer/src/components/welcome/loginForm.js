import React from 'react';
import PropTypes from 'prop-types';
import {
  TextField, Box, Typography, Grid,
} from '@material-ui/core';
import { makeStyles } from '@material-ui/core/styles';
import { LoginButton } from '../../utils/buttons';
import { CHANNELS_PAGE } from '../../constants/constants';

const useStyles = makeStyles(() => ({
  root: {
    display: 'flex',
    flexWrap: 'wrap',
    width: '100%',
  },
}));

const LoginForm = (props) => {
  const classes = useStyles();

  const {
    errors,
    values,
    handleSubmit,
    handleChange,
    pageChanger,
  } = props;

  function setAuthentication(authenticated) {
    if (authenticated === true) {
      pageChanger({ page: CHANNELS_PAGE });
    }
  }

  /*
    @Dylan these are imported from older PANIC version,
    I'm not sure what they were used for but I do not believe
    they are currently needed.
  */
  function handleSetCredentialsValid(setCredentials) {
    console.log(setCredentials);
  }

  function handleSetValidated(setValidated) {
    console.log(setValidated);
  }

  return (
    <div>
      <form onSubmit={handleSubmit} className={classes.root}>
        <Grid container spacing={3} justify="center" alignItems="center">
          <Grid item xs={2}>
            <Typography> Username: </Typography>
          </Grid>
          <Grid item xs={10}>
            <TextField
              error={!errors.username !== true}
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
              error={!errors.password !== true}
              value={values.password}
              type="password"
              name="password"
              placeholder="*****************"
              helperText={errors.password ? errors.password : ''}
              onChange={handleChange}
              fullWidth
            />
          </Grid>
          <Grid item xs={12} />
          <Grid item xs={8} />
          <Grid item xs={4}>
            <Grid container direction="row" justify="flex-end" alignItems="center">
              <Box px={2}>
                <LoginButton
                  username={values.username}
                  password={values.password}
                  disabled={!(Object.keys(errors).length === 0)}
                  setAuthentication={setAuthentication}
                  handleSetCredentialsValid={handleSetCredentialsValid}
                  handleSetValidated={handleSetValidated}
                />
              </Box>
            </Grid>
          </Grid>
        </Grid>
      </form>
    </div>
  );
};

LoginForm.propTypes = {
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
  pageChanger: PropTypes.func.isRequired,
};

export default LoginForm;
