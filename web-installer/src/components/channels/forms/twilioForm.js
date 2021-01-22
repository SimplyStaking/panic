import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import {
  TextField, Box, Typography, Grid, Tooltip,
} from '@material-ui/core';
import Button from 'components/material_ui/CustomButtons/Button';
import Divider from '@material-ui/core/Divider';
import InfoIcon from '@material-ui/icons/Info';
import { MuiThemeProvider } from '@material-ui/core/styles';
import { Autocomplete } from '@material-ui/lab';
import { TestCallButton } from 'utils/buttons';
import { defaultTheme, theme } from 'components/theme/default';
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
                  error={errors.channel_name}
                  value={values.channel_name}
                  type="text"
                  name="channel_name"
                  placeholder="twilio_caller_main"
                  helperText={errors.channel_name ? errors.channel_name : ''}
                  onChange={handleChange}
                  autoComplete="off"
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
                  autoComplete="off"
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
                  error={errors.auth_token}
                  value={values.auth_token}
                  type="text"
                  name="auth_token"
                  placeholder="1234abcd5678efgh1234abcd5678efgh"
                  helperText={errors.auth_token ? errors.auth_token : ''}
                  onChange={handleChange}
                  autoComplete="off"
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
                  error={errors.twilio_phone_no}
                  value={values.twilio_phone_no}
                  type="text"
                  name="twilio_phone_no"
                  placeholder="+12025551234"
                  helperText={
                    errors.twilio_phone_no ? errors.twilio_phone_no : ''
                  }
                  onChange={handleChange}
                  autoComplete="off"
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
                  value={values.twilio_phone_numbers_to_dial_valid}
                  renderInput={(params) => (
                    <TextField
                      // eslint-disable-next-line react/jsx-props-no-spreading
                      {...params}
                      error={errors.twilio_phone_numbers_to_dial_valid}
                      type="text"
                      name="twilio_phone_numbers_to_dial_valid"
                      placeholder={
                        'Add Phone Numbers [Press Enter after each Number]'
                      }
                      variant="standard"
                      helperText={
                        errors.twilio_phone_numbers_to_dial_valid
                          ? errors.twilio_phone_numbers_to_dial_valid
                          : ''
                      }
                      autoComplete="off"
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
                <Grid
                  container
                  direction="row"
                  justify="flex-end"
                  alignItems="center"
                >
                  <Box px={2}>
                    <TestCallButton
                      disabled={Object.keys(errors).length !== 0}
                      twilio_phone_numbers_to_dial_valid={
                        values.twilio_phone_numbers_to_dial_valid
                          ? values.twilio_phone_numbers_to_dial_valid
                          : []
                      }
                      account_sid={values.account_sid}
                      auth_token={values.auth_token}
                      twilio_phone_no={values.twilio_phone_no}
                    />
                    <Button
                      color="primary"
                      size="md"
                      disabled={Object.keys(errors).length !== 0}
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
});

export default TwilioForm;
