import React from 'react';
import { makeStyles, MuiThemeProvider } from '@material-ui/core/styles';
import InputAdornment from '@material-ui/core/InputAdornment';
import PropTypes from 'prop-types';
import forbidExtraProps from 'airbnb-prop-types';
import GridContainer from 'components/material_ui/Grid/GridContainer.js';
import GridItem from 'components/material_ui/Grid/GridItem.js';
import Card from 'components/material_ui/Card/Card.js';
import CardHeader from 'components/material_ui/Card/CardHeader.js';
import CardBody from 'components/material_ui/Card/CardBody.js';
import CardFooter from 'components/material_ui/Card/CardFooter.js';
import CustomInput from 'components/material_ui/CustomInput/CustomInput.js';
import styles from 'assets/jss/material-kit-react/views/componentsSections/loginStyle.js';

import { Tooltip } from '@material-ui/core';
import { theme } from 'components/theme/default';
import InfoIcon from '@material-ui/icons/Info';
import StartDialog from 'components/welcome/startDialog';
import Data from 'data/welcome';

const useStyles = makeStyles(styles);

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
    <div>
      <div className={classes.container}>
        <GridContainer justify="center">
          <GridItem xs={12} sm={12} md={4}>
            <Card>
              <form onSubmit={handleSubmit} className={classes.form}>
                <CardHeader color="primary" className={classes.cardHeader}>
                  <h2>Login</h2>
                </CardHeader>
                <CardBody>
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
                    inputProps={{
                      endAdornment: (
                        <InputAdornment position="end">
                          <MuiThemeProvider theme={theme}>
                            <Tooltip title={Data.username} placement="left">
                              <InfoIcon />
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
                    inputProps={{
                      endAdornment: (
                        <InputAdornment position="end">
                          <MuiThemeProvider theme={theme}>
                            <Tooltip title={Data.password} placement="left">
                              <InfoIcon />
                            </Tooltip>
                          </MuiThemeProvider>
                        </InputAdornment>
                      ),
                      autoComplete: 'off',
                    }}
                  />
                </CardBody>
                <CardFooter className={classes.cardFooter}>
                  <StartDialog
                    values={values}
                    errors={errors}
                    pageChanger={pageChanger}
                    authenticate={authenticate}
                    checkForConfigs={checkForConfigs}
                    loadUsersFromMongo={loadUsersFromMongo}
                    addUserRedux={addUserRedux}
                  />
                </CardFooter>
              </form>
            </Card>
          </GridItem>
        </GridContainer>
      </div>
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
