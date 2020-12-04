import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import {
  TextField, Box, Checkbox, FormControlLabel, Typography, Switch, Grid, Tooltip,
} from '@material-ui/core';
import Button from "components/material_ui/CustomButtons/Button.js";
import { MuiThemeProvider } from '@material-ui/core/styles';
import InfoIcon from '@material-ui/icons/Info';
import Divider from '@material-ui/core/Divider';
import { SendTestAlertButton } from 'utils/buttons';
import { defaultTheme, theme } from 'components/theme/default';
import Data from 'data/channels';

const TelegramForm = ({errors, values, handleSubmit, handleChange, setFieldValue
  }) => {
  return (
    <MuiThemeProvider theme={defaultTheme}>
      <div>
        <Typography
          variant="subtitle1"
          gutterBottom
          className="greyBackground">
          <Box m={2} p={3}>
            <p>{Data.telegram.description}</p>
          </Box>
        </Typography>
        <Divider />
        <form onSubmit={handleSubmit} className="root">
          <Box p={3}>
            <Grid container spacing={3} justify="center" alignItems="center">
              <Grid item xs={2}>
                <Typography> Bot Name </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  error={errors.bot_name}
                  value={values.bot_name}
                  type="text"
                  name="bot_name"
                  placeholder={Data.telegram.bot_namePlaceholder}
                  helperText={errors.bot_name ? errors.bot_name : ''}
                  onChange={handleChange}
                  autoComplete='off'
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={Data.telegram.name} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={2}>
                <Typography> Bot Token </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  error={errors.bot_token}
                  value={values.bot_token}
                  type="text"
                  name="bot_token"
                  placeholder={Data.telegram.botTokenPlaceholder}
                  helperText={errors.bot_token ? errors.bot_token : ''}
                  onChange={handleChange}
                  autoComplete='off'
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={Data.telegram.token} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={2}>
                <Typography> Chat ID </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  error={errors.chat_id}
                  value={values.chat_id}
                  type="text"
                  name="chat_id"
                  placeholder={Data.telegram.chatIdPlaceholder}
                  helperText={errors.chat_id ? errors.chat_id : ''}
                  onChange={handleChange}
                  autoComplete='off'
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={Data.telegram.chat_id} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={2}>
                <Typography> Severities </Typography>
              </Grid>
              <Grid item xs={9}>
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
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={Data.telegram.severities} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={2}>
                <Typography> Telegram Commands </Typography>
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={Data.telegram.commands} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
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
              <Grid item xs={2}>
                <Typography> Telegram Alerts </Typography>
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={Data.telegram.alerts} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
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
                <Grid
                  container
                  direction="row"
                  justify="flex-end"
                  alignItems="center">
                  <Box px={2}>
                    <SendTestAlertButton
                      disabled={(Object.keys(errors).length !== 0)}
                      botChatID={values.chat_id}
                      bot_token={values.bot_token}
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

TelegramForm.propTypes = forbidExtraProps({
  errors: PropTypes.shape({
    bot_name: PropTypes.string,
    bot_token: PropTypes.string,
    chat_id: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    bot_name: PropTypes.string.isRequired,
    bot_token: PropTypes.string.isRequired,
    chat_id: PropTypes.string.isRequired,
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
