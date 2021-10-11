import React from 'react';
import { MuiThemeProvider } from '@material-ui/core/styles';
import InputAdornment from '@material-ui/core/InputAdornment';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import Grid from '@material-ui/core/Grid';
import CustomInput from 'components/material_ui/CustomInput/CustomInput';
import useStyles from 'assets/jss/material-kit-react/views/componentsSections/loginStyle';

import { Tooltip } from '@material-ui/core';
import { theme } from 'components/theme/default';
import { AccountCircle, LockRounded } from '@material-ui/icons';
import StartDialog from 'components/welcome/startDialog';
import PanicLogo from 'assets/img/logos/panicLogo.png';
import Data from 'data/welcome';

const LoginForm = ({
  errors,
  values,
  handleSubmit,
  handleChange,
  pageChanger,
  authenticate,
  checkForConfigs,
  loadUsersFromMongo,
  addUserRedux,
}) => {
  const classes = useStyles();

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        maxWidth: 400,
        minWidth: 300,
      }}
    >
      <form onSubmit={handleSubmit} className={classes.form}>
        <Grid container justify="center">
          <img
            src={PanicLogo}
            alt="PANIC Logo"
            width={300}
          />
        </Grid>
        <CustomInput
          error={errors.username}
          value={values.username}
          helperText=""
          handleChange={handleChange}
          name="username"
          placeHolder="Username"
          id="username"
          type="text"
          formControlProps={{
            fullWidth: true,
          }}
          label="Username"
          inputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <MuiThemeProvider theme={theme}>
                  <Tooltip title={Data.username} placement="left">
                    <AccountCircle />
                  </Tooltip>
                </MuiThemeProvider>
              </InputAdornment>
            ),
          }}
        />
        <CustomInput
          error={errors.password}
          value={values.password}
          helperText=""
          handleChange={handleChange}
          name="password"
          placeHolder="Password"
          id="password"
          type="password"
          formControlProps={{
            fullWidth: true,
          }}
          label="Password"
          inputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <MuiThemeProvider theme={theme}>
                  <Tooltip title={Data.password} placement="left">
                    <LockRounded />
                  </Tooltip>
                </MuiThemeProvider>
              </InputAdornment>
            ),
            autoComplete: 'off',
          }}
        />
        <div style={{ height: 20 }} />
        <StartDialog
          values={values}
          errors={errors}
          pageChanger={pageChanger}
          authenticate={authenticate}
          checkForConfigs={checkForConfigs}
          loadUsersFromMongo={loadUsersFromMongo}
          addUserRedux={addUserRedux}
        />
      </form>
    </div>
  );
};

LoginForm.propTypes = forbidExtraProps({
  checkForConfigs: PropTypes.func.isRequired,
  loadUsersFromMongo: PropTypes.func.isRequired,
  addUserRedux: PropTypes.func.isRequired,
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
});

export default LoginForm;
