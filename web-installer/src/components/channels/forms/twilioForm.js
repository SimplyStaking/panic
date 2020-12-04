import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import { TextField, Box, Typography, Grid, Tooltip } from '@material-ui/core';
import Button from "components/material_ui/CustomButtons/Button.js";
import Divider from '@material-ui/core/Divider';
import InfoIcon from '@material-ui/icons/Info';
import { MuiThemeProvider } from '@material-ui/core/styles';
import { Autocomplete } from '@material-ui/lab';
import { TestCallButton } from 'utils/buttons';
import { defaultTheme, theme } from 'components/theme/default';
import Data from 'data/channels';

const TwilioForm = ({errors, values, handleSubmit, handleChange, setFieldValue
  }) => {

  const updateTwilioNumbers = (events, phoneNums) => {
    setFieldValue('twilioPhoneNumbersToDial', phoneNums);
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
                <Typography> Configuration Name </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  error={errors.config_name}
                  value={values.config_name}
                  type="text"
                  name="config_name"
                  placeholder="twilio_caller_main"
                  helperText={errors.config_name ? errors.config_name : ''}
                  onChange={handleChange}
                  inputProps={{min: 0, style: { textAlign: 'right' }}}
                  autoComplete='off'
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
                <Typography> Account Sid </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  error={errors.account_sid}
                  value={values.account_sid}
                  type="text"
                  name="account_sid"
                  placeholder="abcd1234efgh5678ABCD1234EFGH567890"
                  helperText={errors.account_sid ? errors.account_sid : ''}
                  onChange={handleChange}
                  inputProps={{min: 0, style: { textAlign: 'right' }}}
                  autoComplete='off'
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
                <Typography> Authentication Token </Typography>
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
                  inputProps={{min: 0, style: { textAlign: 'right' }}}
                  autoComplete='off'
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
                <Typography> Twilio Phone Number </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  error={errors.twilioPhoneNum}
                  value={values.twilioPhoneNum}
                  type="text"
                  name="twilioPhoneNum"
                  placeholder="+12025551234"
                  helperText={errors.twilioPhoneNum ? errors.twilioPhoneNum : ''}
                  onChange={handleChange}
                  inputProps={{min: 0, style: { textAlign: 'right' }}}
                  autoComplete='off'
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
                <Typography> Phone numbers to dial </Typography>
              </Grid>
              <Grid item xs={9}>
                <Autocomplete
                  multiple
                  freeSolo
                  options={[]}
                  onChange={updateTwilioNumbers}
                  value={values.twilioPhoneNumbersToDial}
                  renderInput={(params) => (
                    <TextField
                      // eslint-disable-next-line react/jsx-props-no-spreading
                      {...params}
                      error={errors.twilioPhoneNumbersToDial}
                      type="text"
                      name="twilioPhoneNumbersToDial"
                      placeholder="Add Phone Numbers [Press Enter after each Number]"
                      variant="standard"
                      helperText={errors.twilioPhoneNumbersToDial ? errors.twilioPhoneNumbersToDial : ''}
                      autoComplete='off'
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
                      twilioPhoneNumbersToDial={
                        values.twilioPhoneNumbersToDial
                          ? values.twilioPhoneNumbersToDial : []
                      }
                      account_sid={values.account_sid}
                      authToken={values.authToken}
                      twilioPhoneNum={values.twilioPhoneNum}
                    />
                    <Button
                      color="primary"
                      size="md"
                      disabled={(Object.keys(errors).length !== 0)}
                      type="submit"
                    >
                      Add
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
    config_name: PropTypes.string,
    account_sid: PropTypes.string,
    authToken: PropTypes.string,
    twilioPhoneNum: PropTypes.string,
    twilioPhoneNumbersToDial: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    config_name: PropTypes.string.isRequired,
    account_sid: PropTypes.string.isRequired,
    authToken: PropTypes.string.isRequired,
    twilioPhoneNum: PropTypes.string.isRequired,
    twilioPhoneNumbersToDial: PropTypes.arrayOf(
      PropTypes.string.isRequired,
    ).isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
  setFieldValue: PropTypes.func.isRequired,
});

export default TwilioForm;
