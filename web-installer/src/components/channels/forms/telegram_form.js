import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import {
  TextField, Button, Box, Checkbox, FormControlLabel, Typography, Switch,
} from '@material-ui/core';
import Grid from '@material-ui/core/Grid';
import { makeStyles } from '@material-ui/core/styles';
import SendTestAlertButton from '../../../containers/channels/buttons';

const useStyles = makeStyles(() => ({
  root: {
    display: 'flex',
    flexWrap: 'wrap',
    width: '100%',
  },
}));

const TelegramForm = (props) => {
  const classes = useStyles();

  const {
    errors,
    values,
    handleSubmit,
    handleChange,
    setFieldValue,
  } = props;

  return (
    <div>
      <form onSubmit={handleSubmit} className={classes.root}>
        <Grid container spacing={3} justify="center" alignItems="center">
          <Grid item xs={2}>
            <Typography> Bot Name: </Typography>
          </Grid>
          <Grid item xs={10}>
            <TextField
              error={!errors.botName !== true}
              value={values.botName}
              type="text"
              name="botName"
              placeholder="telegram_chat_1"
              helperText={errors.botName ? errors.botName : ''}
              onChange={handleChange}
              fullWidth
            />
          </Grid>
          <Grid item xs={2}>
            <Typography> Bot Token: </Typography>
          </Grid>
          <Grid item xs={10}>
            <TextField
              error={!errors.botToken !== true}
              value={values.botToken}
              type="text"
              name="botToken"
              placeholder="123456789:ABCDEF-1234abcd5678efgh12345_abc123"
              helperText={errors.botToken ? errors.botToken : ''}
              onChange={handleChange}
              fullWidth
            />
          </Grid>
          <Grid item xs={2}>
            <Typography> Chat ID: </Typography>
          </Grid>
          <Grid item xs={10}>
            <TextField
              error={!errors.chatID !== true}
              value={values.chatID}
              type="text"
              name="chatID"
              placeholder="-123456789"
              helperText={errors.chatID ? errors.chatID : ''}
              onChange={handleChange}
              fullWidth
            />
          </Grid>
          <Grid item xs={2}>
            <Typography> Severities: </Typography>
          </Grid>
          <Grid item xs={10}>
            <FormControlLabel
              control={(
                <Checkbox
                  checked={values.info}
                  onChange={handleChange}
                  name="info"
                  color="primary"
                />
              )}
              label="Info"
              labelPlacement="start"
            />
            <FormControlLabel
              control={(
                <Checkbox
                  checked={values.warning}
                  onChange={handleChange}
                  name="warning"
                  color="primary"
                />
              )}
              label="Warning"
              labelPlacement="start"
            />
            <FormControlLabel
              control={(
                <Checkbox
                  checked={values.critical}
                  onChange={handleChange}
                  name="critical"
                  color="primary"
                />
              )}
              label="Critical"
              labelPlacement="start"
            />
            <FormControlLabel
              control={(
                <Checkbox
                  checked={values.error}
                  onChange={handleChange}
                  name="error"
                  color="primary"
                />
              )}
              label="Error"
              labelPlacement="start"
            />
          </Grid>
          <Grid item xs={3}>
            <Typography> Telegram Commands: </Typography>
          </Grid>
          <Grid item xs={1}>
            <FormControlLabel
              control={(
                <Switch
                  checked={values.commands}
                  onClick={() => {
                    setFieldValue('commands', !values.commands);
                  }}
                  name="telegramCommands"
                  color="primary"
                />
              )}
            />
          </Grid>
          <Grid item xs={3}>
            <Typography> Telegram Alerts: </Typography>
          </Grid>
          <Grid item xs={1}>
            <FormControlLabel
              control={(
                <Switch
                  checked={values.alerts}
                  onClick={() => {
                    setFieldValue('alerts', !values.alerts);
                  }}
                  name="telegramAlerts"
                  color="primary"
                />
              )}
            />
          </Grid>
          <Grid item xs={4}>
            <Grid container direction="row" justify="flex-end" alignItems="center">
              <Box px={2}>
                <SendTestAlertButton
                  disabled={!(Object.keys(errors).length === 0)}
                  botChatID={values.chatID}
                  botToken={values.botToken}
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

TelegramForm.propTypes = forbidExtraProps({
  errors: PropTypes.shape({
    botName: PropTypes.string,
    botToken: PropTypes.string,
    chatID: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    botName: PropTypes.string.isRequired,
    botToken: PropTypes.string.isRequired,
    chatID: PropTypes.string.isRequired,
    info: PropTypes.bool.isRequired,
    warning: PropTypes.bool.isRequired,
    critical: PropTypes.bool.isRequired,
    error: PropTypes.bool.isRequired,
    alerts: PropTypes.bool.isRequired,
    commands: PropTypes.bool.isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
  setFieldValue: PropTypes.func.isRequired,
});

export default TelegramForm;
