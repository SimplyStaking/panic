import React from 'react';
import PropTypes from 'prop-types';
import {
  TextField, Box, Typography, Grid, Tooltip,
} from '@material-ui/core';
import { MuiThemeProvider } from '@material-ui/core/styles';
import InfoIcon from '@material-ui/icons/Info';
import { LoginButton } from '../../utils/buttons';
import { CHANNELS_PAGE } from '../../constants/constants';
import { defaultTheme, theme, useStyles } from '../theme/default';
import Data from '../../data/welcome';

const LoginForm = (props) => {
  const classes = useStyles();

  const {
    errors,
    values,
    handleSubmit,
    handleChange,
    pageChanger,
    authenticate,
  } = props;

  // If authenetication is accepted by the backend, change the page
  // to the channels setup and set authenticated.
  function setAuthentication(authenticated) {
    if (authenticated === true) {
      pageChanger({ page: CHANNELS_PAGE });
      authenticate(authenticated);
    }
  }

  return (
    <MuiThemeProvider theme={defaultTheme}>
      <div>
        <form onSubmit={handleSubmit} className={classes.root}>
          <Grid container spacing={3} justify="center" alignItems="center">
            <Grid item xs={2}>
              <Typography> Username: </Typography>
            </Grid>
            <Grid item xs={9}>
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
            <Grid item xs={1}>
              <Grid container justify="center">
                <MuiThemeProvider theme={theme}>
                  <Tooltip title={Data.welcome.username} placement="left">
                    <InfoIcon />
                  </Tooltip>
                </MuiThemeProvider>
              </Grid>
            </Grid>
            <Grid item xs={2}>
              <Typography> Password: </Typography>
            </Grid>
            <Grid item xs={9}>
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
            <Grid item xs={1}>
              <Grid container justify="center">
                <MuiThemeProvider theme={theme}>
                  <Tooltip title={Data.welcome.password} placement="left">
                    <InfoIcon />
                  </Tooltip>
                </MuiThemeProvider>
              </Grid>
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
                  />
                </Box>
              </Grid>
            </Grid>
          </Grid>
        </form>
      </div>
    </MuiThemeProvider>
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
  authenticate: PropTypes.func.isRequired,
};

export default LoginForm;
