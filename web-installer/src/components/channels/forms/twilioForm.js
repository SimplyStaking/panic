import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import {
  TextField, Button, Box, Typography, Grid, Tooltip,
} from '@material-ui/core';
import Divider from '@material-ui/core/Divider';
import InfoIcon from '@material-ui/icons/Info';
import { MuiThemeProvider } from '@material-ui/core/styles';
import { Autocomplete } from '@material-ui/lab';
import { TestCallButton } from '../../../utils/buttons';
import { defaultTheme, theme } from '../../theme/default';
import Data from '../../../data/channels';

const TwilioForm = ({errors, values, handleSubmit, handleChange, setFieldValue
  }) => {

  const updateTwilioNumbers = (events, phoneNums) => {
    setFieldValue('twilioPhoneNumbersToDialValid', phoneNums);
  };

  return (
    <MuiThemeProvider theme={defaultTheme}>
      <div>
        <Typography variant="subtitle1" gutterBottom className="greyBackground">
          <Box m={2} p={3}>
            <p>{Data.twilio.description}</p>
          </Box>
        </Typography>
        <Divider />
        <form onSubmit={handleSubmit} className="root">
          <Box p={3}>
            <Grid container spacing={3} justify="center" alignItems="center">
              <Grid item xs={2}>
                <Typography> Configuration Name: </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  error={errors.configName}
                  value={values.configName}
                  type="text"
                  name="configName"
                  placeholder="twilio_caller_main"
                  helperText={errors.configName ? errors.configName : ''}
                  onChange={handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={Data.twilio.name} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={2}>
                <Typography> Account Sid: </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  error={errors.accountSid}
                  value={values.accountSid}
                  type="text"
                  name="accountSid"
                  placeholder="abcd1234efgh5678ABCD1234EFGH567890"
                  helperText={errors.accountSid ? errors.accountSid : ''}
                  onChange={handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={Data.twilio.account} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={2}>
                <Typography> Authentication Token: </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  error={errors.authToken}
                  value={values.authToken}
                  type="text"
                  name="authToken"
                  placeholder="1234abcd5678efgh1234abcd5678efgh"
                  helperText={errors.authToken ? errors.authToken : ''}
                  onChange={handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={Data.twilio.token} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={2}>
                <Typography> Twilio Phone Number: </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  error={errors.twilioPhoneNo}
                  value={values.twilioPhoneNo}
                  type="text"
                  name="twilioPhoneNo"
                  placeholder="+12025551234"
                  helperText={errors.twilioPhoneNo ? errors.twilioPhoneNo : ''}
                  onChange={handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={Data.twilio.phoneNumber} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={2}>
                <Typography> Phone numbers to dial: </Typography>
              </Grid>
              <Grid item xs={9}>
                <Autocomplete
                  multiple
                  freeSolo
                  options={[]}
                  onChange={updateTwilioNumbers}
                  value={values.twilioPhoneNumbersToDialValid}
                  renderInput={(params) => (
                    <TextField
                      // eslint-disable-next-line react/jsx-props-no-spreading
                      {...params}
                      error={errors.twilioPhoneNumbersToDialValid}
                      type="text"
                      name="twilioPhoneNumbersToDialValid"
                      placeholder="Add Phone Numbers"
                      variant="standard"
                      helperText={errors.twilioPhoneNumbersToDialValid ? errors.twilioPhoneNumbersToDialValid : ''}
                      fullWidth
                    />
                  )}
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={Data.twilio.dialNumbers} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={8} />
              <Grid item xs={4}>
                <Grid container direction="row" justify="flex-end" alignItems="center">
                  <Box px={2}>
                    <TestCallButton
                      disabled={(Object.keys(errors).length !== 0)}
                      twilioPhoneNumbersToDialValid={
                        values.twilioPhoneNumbersToDialValid
                          ? values.twilioPhoneNumbersToDialValid : []
                      }
                      accountSid={values.accountSid}
                      authToken={values.authToken}
                      twilioPhoneNo={values.twilioPhoneNo}
                    />
                    <Button
                      variant="outlined"
                      size="large"
                      disabled={(Object.keys(errors).length !== 0)}
                      type="submit"
                    >
                      <Box px={2}>
                        Add
                      </Box>
                    </Button>
                  </Box>
                </Grid>
              </Grid>
            </Grid>
          </Box>
        </form>
      </div>
    </MuiThemeProvider>
  );
};

TwilioForm.propTypes = forbidExtraProps({
  errors: PropTypes.shape({
    configName: PropTypes.string,
    accountSid: PropTypes.string,
    authToken: PropTypes.string,
    twilioPhoneNo: PropTypes.string,
    twilioPhoneNumbersToDialValid: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    configName: PropTypes.string.isRequired,
    accountSid: PropTypes.string.isRequired,
    authToken: PropTypes.string.isRequired,
    twilioPhoneNo: PropTypes.string.isRequired,
    twilioPhoneNumbersToDialValid: PropTypes.arrayOf(
      PropTypes.string.isRequired,
    ).isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
  setFieldValue: PropTypes.func.isRequired,
});

export default TwilioForm;
