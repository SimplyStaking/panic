import React from 'react';
import PropTypes from 'prop-types';
import {
  TextField, Button, Box, Typography,
} from '@material-ui/core';
import Grid from '@material-ui/core/Grid';
import { makeStyles } from '@material-ui/core/styles';
import TestCallButton from '../../../containers/channels/buttons';

const useStyles = makeStyles(() => ({
  root: {
    display: 'flex',
    flexWrap: 'wrap',
    width: '100%',
  },
}));

const TwilioForm = (props) => {
  const classes = useStyles();

  const {
    errors,
    values,
    handleSubmit,
    handleChange,
  } = props;

  return (
    <div>
      <form onSubmit={handleSubmit} className={classes.root}>
        <Grid container spacing={3} justify="center" alignItems="center">
          <Grid item xs={2}>
            <Typography> Configuration Name: </Typography>
          </Grid>
          <Grid item xs={10}>
            <TextField
              error={!errors.configName !== true}
              value={values.configName}
              type="text"
              name="configName"
              placeholder="twilio_caller_main"
              helperText={errors.configName ? errors.configName : ''}
              onChange={handleChange}
              fullWidth
            />
          </Grid>
          <Grid item xs={2}>
            <Typography> Account Sid: </Typography>
          </Grid>
          <Grid item xs={10}>
            <TextField
              error={!errors.accountSid !== true}
              value={values.accountSid}
              type="text"
              name="accountSid"
              placeholder="abcd1234efgh5678ABCD1234EFGH567890"
              helperText={errors.accountSid ? errors.accountSid : ''}
              onChange={handleChange}
              fullWidth
            />
          </Grid>
          <Grid item xs={2}>
            <Typography> Authentication Token: </Typography>
          </Grid>
          <Grid item xs={10}>
            <TextField
              error={!errors.authToken !== true}
              value={values.authToken}
              type="text"
              name="authToken"
              placeholder="1234abcd5678efgh1234abcd5678efgh"
              helperText={errors.authToken ? errors.authToken : ''}
              onChange={handleChange}
              fullWidth
            />
          </Grid>
          <Grid item xs={2}>
            <Typography> Twilio Phone Number: </Typography>
          </Grid>
          <Grid item xs={10}>
            <TextField
              error={!errors.twilioPhoneNo !== true}
              value={values.twilioPhoneNo}
              type="text"
              name="twilioPhoneNo"
              placeholder="+12025551234"
              helperText={errors.twilioPhoneNo ? errors.twilioPhoneNo : ''}
              onChange={handleChange}
              fullWidth
            />
          </Grid>
          <Grid item xs={2}>
            <Typography> Phone numbers to dial: </Typography>
          </Grid>
          <Grid item xs={10}>
            <TextField
              error={!errors.phoneNoToDial !== true}
              value={values.phoneNoToDial}
              type="text"
              name="phoneNoToDial"
              placeholder="+12025551234"
              helperText={errors.phoneNoToDial ? errors.phoneNoToDial : ''}
              onChange={handleChange}
              fullWidth
            />
          </Grid>
          <Grid item xs={8} />
          <Grid item xs={4}>
            <Grid container direction="row" justify="flex-end" alignItems="center">
              <Box px={2}>
                <TestCallButton
                  disabled={!(Object.keys(errors).length === 0)}
                  phoneNoToDial={values.phoneNoToDial.split(';')[0]}
                  accountSid={values.accountSid}
                  authToken={values.authToken}
                  twilioPhoneNo={values.twilioPhoneNo}
                />
                <Button
                  variant="outlined"
                  size="large"
                  disabled={!(Object.keys(errors).length === 0)}
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
      </form>
    </div>
  );
};

TwilioForm.propTypes = {
  errors: PropTypes.shape({
    configName: PropTypes.string,
    accountSid: PropTypes.string,
    authToken: PropTypes.string,
    twilioPhoneNo: PropTypes.string,
    phoneNoToDial: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    configName: PropTypes.string.isRequired,
    accountSid: PropTypes.string.isRequired,
    authToken: PropTypes.string.isRequired,
    twilioPhoneNo: PropTypes.string.isRequired,
    phoneNoToDial: PropTypes.string.isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
};

export default TwilioForm;
