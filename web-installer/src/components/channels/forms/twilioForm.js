import React from 'react';
import PropTypes from 'prop-types';
import {
  Box, Typography, Grid, Tooltip, InputAdornment,
} from '@material-ui/core';
import Button from 'components/material_ui/CustomButtons/Button';
import Divider from '@material-ui/core/Divider';
import InfoIcon from '@material-ui/icons/Info';
import { MuiThemeProvider } from '@material-ui/core/styles';
import { Autocomplete } from '@material-ui/lab';
import { TestCallButton } from 'utils/buttons';
import { defaultTheme, theme } from 'components/theme/default';
import CssTextField from 'assets/jss/custom-jss/CssTextField';
import Data from 'data/channels';

const TwilioForm = ({
  errors,
  values,
  handleSubmit,
  handleChange,
  setFieldValue,
}) => {
  const updateTwilioNumbers = (events, phoneNums) => {
    setFieldValue('twilio_phone_numbers_to_dial_valid', phoneNums);
  };

  return (
    <MuiThemeProvider theme={defaultTheme}>
      <div className="greyBackground">
        <Typography variant="subtitle1" gutterBottom>
          <Box m={2} pt={3} px={3}>
            <p
              style={{
                fontWeight: '350',
                fontSize: '1.2rem',
              }}
            >
              {Data.twilio.description}
            </p>
          </Box>
        </Typography>
        <Divider />
        <form onSubmit={handleSubmit} className="root">
          <Box m={2} p={3}>
            <Grid container spacing={1} justifyContent="center" alignItems="center">
              <Grid item xs={12}>
                <CssTextField
                  id="channel-name-outlined-full-width"
                  error={!!(errors.channel_name)}
                  value={values.channel_name}
                  label="Configuration Name"
                  type="text"
                  style={{ margin: 8 }}
                  name="channel_name"
                  placeholder={Data.twilio.channelNamePlaceholder}
                  helperText={errors.channel_name ? errors.channel_name : ''}
                  onChange={handleChange}
                  fullWidth
                  margin="normal"
                  InputLabelProps={{
                    shrink: true,
                  }}
                  variant="outlined"
                  autoComplete="off"
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <MuiThemeProvider theme={theme}>
                          <Tooltip title={Data.twilio.name} placement="left">
                            <InfoIcon />
                          </Tooltip>
                        </MuiThemeProvider>
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              <Grid item xs={12}>
                <CssTextField
                  id="account-sid-outlined-full-width"
                  error={!!(errors.account_sid)}
                  value={values.account_sid}
                  label="Account SID"
                  type="text"
                  style={{ margin: 8 }}
                  name="account_sid"
                  placeholder={Data.twilio.accountSidPlaceholder}
                  helperText={errors.account_sid ? errors.account_sid : ''}
                  onChange={handleChange}
                  fullWidth
                  margin="normal"
                  InputLabelProps={{
                    shrink: true,
                  }}
                  variant="outlined"
                  autoComplete="off"
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <MuiThemeProvider theme={theme}>
                          <Tooltip title={Data.twilio.account} placement="left">
                            <InfoIcon />
                          </Tooltip>
                        </MuiThemeProvider>
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              <Grid item xs={12}>
                <CssTextField
                  id="authentication-token-outlined-full-width"
                  error={!!(errors.auth_token)}
                  value={values.auth_token}
                  label="Authentication Token"
                  type="text"
                  style={{ margin: 8 }}
                  name="auth_token"
                  placeholder={Data.twilio.authTokenPlaceholder}
                  helperText={errors.auth_token ? errors.auth_token : ''}
                  onChange={handleChange}
                  fullWidth
                  margin="normal"
                  InputLabelProps={{
                    shrink: true,
                  }}
                  variant="outlined"
                  autoComplete="off"
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <MuiThemeProvider theme={theme}>
                          <Tooltip title={Data.twilio.token} placement="left">
                            <InfoIcon />
                          </Tooltip>
                        </MuiThemeProvider>
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              <Grid item xs={12}>
                <CssTextField
                  id="twilio-phone-number-outlined-full-width"
                  error={!!(errors.twilio_phone_no)}
                  value={values.twilio_phone_no}
                  label="Twilio Phone Number"
                  type="text"
                  style={{ margin: 8 }}
                  name="twilio_phone_no"
                  placeholder={Data.twilio.twilioNumberPlaceholder}
                  helperText={errors.twilio_phone_no ? errors.twilio_phone_no : ''}
                  onChange={handleChange}
                  fullWidth
                  margin="normal"
                  InputLabelProps={{
                    shrink: true,
                  }}
                  variant="outlined"
                  autoComplete="off"
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <MuiThemeProvider theme={theme}>
                          <Tooltip title={Data.twilio.phoneNumber} placement="left">
                            <InfoIcon />
                          </Tooltip>
                        </MuiThemeProvider>
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              <Grid item xs={12}>
                <Autocomplete
                  multiple
                  freeSolo
                  options={[]}
                  onChange={updateTwilioNumbers}
                  value={values.twilio_phone_numbers_to_dial_valid}
                  renderInput={(params) => (
                    <CssTextField
                      // eslint-disable-next-line react/jsx-props-no-spreading
                      {...params}
                      id="twilio-phone-numbers-to-dial-outlined-full-width"
                      error={!!(errors.twilio_phone_numbers_to_dial_valid)}
                      value={values.twilio_phone_numbers_to_dial_valid}
                      label="Phone numbers for Twilio to dial"
                      type="text"
                      style={{ margin: 8 }}
                      name="twilio_phone_numbers_to_dial_valid"
                      placeholder={Data.twilio.twilioPhoneNumbersToDialValid}
                      helperText={errors.twilio_phone_no ? errors.twilio_phone_no : ''}
                      fullWidth
                      margin="normal"
                      InputLabelProps={{
                        shrink: true,
                      }}
                      variant="outlined"
                      autoComplete="off"
                    />
                  )}
                />
              </Grid>
              <Grid item xs={8} />
              <Grid item xs={4}>
                <Grid
                  container
                  direction="row"
                  justifyContent="flex-end"
                >
                  <TestCallButton
                    disabled={Object.keys(errors).length !== 0}
                    twilioPhoneNumbersToDialValid={
                      values.twilio_phone_numbers_to_dial_valid
                        ? values.twilio_phone_numbers_to_dial_valid
                        : []
                    }
                    accountSid={values.account_sid}
                    authToken={values.auth_token}
                    twilioPhoneNumber={values.twilio_phone_no}
                  />
                  <Button
                    color="primary"
                    size="md"
                    disabled={Object.keys(errors).length !== 0}
                    type="submit"
                  >
                    Add
                  </Button>
                </Grid>
              </Grid>
            </Grid>
          </Box>
        </form>
      </div>
    </MuiThemeProvider>
  );
};

TwilioForm.propTypes = {
  errors: PropTypes.shape({
    channel_name: PropTypes.string,
    account_sid: PropTypes.string,
    auth_token: PropTypes.string,
    twilio_phone_no: PropTypes.string,
    twilio_phone_numbers_to_dial_valid: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    channel_name: PropTypes.string.isRequired,
    account_sid: PropTypes.string.isRequired,
    auth_token: PropTypes.string.isRequired,
    twilio_phone_no: PropTypes.string.isRequired,
    twilio_phone_numbers_to_dial_valid: PropTypes.arrayOf(PropTypes.string.isRequired)
      .isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
  setFieldValue: PropTypes.func.isRequired,
};

export default TwilioForm;
