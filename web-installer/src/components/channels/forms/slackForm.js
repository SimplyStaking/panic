import React from 'react';
import PropTypes from 'prop-types';
import {
  InputAdornment,
  Box,
  Checkbox,
  FormControlLabel,
  Typography,
  Switch,
  Grid,
  Tooltip,
} from '@material-ui/core';
import Button from 'components/material_ui/CustomButtons/Button';
import { MuiThemeProvider } from '@material-ui/core/styles';
import InfoIcon from '@material-ui/icons/Info';
import Divider from '@material-ui/core/Divider';
import { SendTestSlackButton } from 'utils/buttons';
import { defaultTheme, theme } from 'components/theme/default';
import CssTextField from 'assets/jss/custom-jss/CssTextField';
import Data from 'data/channels';

const SlackForm = ({
  errors, values, handleSubmit, handleChange, setFieldValue,
}) => (
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
            {Data.slack.description}
          </p>
        </Box>
      </Typography>
      <Divider />
      <form onSubmit={handleSubmit} className="root">
        <Box m={2} p={4}>
          <Grid container spacing={1} justifyContent="center" alignItems="center">
            <Grid item xs={12}>
              <CssTextField
                id="channel-name-outlined-full-width"
                error={!!(errors.channel_name)}
                value={values.channel_name}
                label="Channel Name"
                type="text"
                style={{ margin: 8 }}
                name="channel_name"
                placeholder={Data.slack.channelNamePlaceholder}
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
                        <Tooltip title={Data.slack.name} placement="left">
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
                id="token-outlined-full-width"
                error={!!(errors.app_token)}
                value={values.app_token}
                label="App-Level Token"
                type="text"
                style={{ margin: 8 }}
                name="app_token"
                placeholder={Data.slack.appTokenPlaceholder}
                helperText={errors.app_token ? errors.app_token : ''}
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
                        <Tooltip title={Data.slack.appToken} placement="left">
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
                id="token-outlined-full-width"
                error={!!(errors.bot_token)}
                value={values.bot_token}
                label="Bot Token"
                type="text"
                style={{ margin: 8 }}
                name="bot_token"
                placeholder={Data.slack.botTokenPlaceholder}
                helperText={errors.bot_token ? errors.bot_token : ''}
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
                        <Tooltip title={Data.slack.botToken} placement="left">
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
                id="slack-chat-name-outlined-full-width"
                error={!!(errors.bot_channel_id)}
                value={values.bot_channel_id}
                label="Bot Channel ID"
                type="text"
                style={{ margin: 8 }}
                name="bot_channel_id"
                placeholder={Data.slack.botChannelIdPlaceholder}
                helperText={errors.bot_channel_id ? errors.bot_channel_id : ''}
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
                        <Tooltip title={Data.slack.botChannelId} placement="left">
                          <InfoIcon />
                        </Tooltip>
                      </MuiThemeProvider>
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid container spacing={1} justifyContent="center" alignItems="center">
              <Grid item xs={2}>
                <Box pl={2}>
                  <Typography variant="subtitle1">Severities</Typography>
                </Box>
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
                <Grid container justifyContent="flex-end">
                  <Box pr={1}>
                    <MuiThemeProvider theme={theme}>
                      <Tooltip title={Data.slack.severities} placement="left">
                        <InfoIcon />
                      </Tooltip>
                    </MuiThemeProvider>
                  </Box>
                </Grid>
              </Grid>
            </Grid>
            <Grid item xs={2}>
              <Box pl={1.5}>
                <Typography> Slack Commands </Typography>
              </Box>
            </Grid>
            <Grid item xs={1}>
              <Grid container justifyContent="center">
                <MuiThemeProvider theme={theme}>
                  <Tooltip title={Data.slack.commands} placement="left">
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
                    name="slackCommands"
                    color="primary"
                  />
                )}
                label=""
              />
            </Grid>
            <Grid item xs={2}>
              <Typography> Slack Alerts </Typography>
            </Grid>
            <Grid item xs={1}>
              <Grid container justifyContent="center">
                <MuiThemeProvider theme={theme}>
                  <Tooltip title={Data.slack.alerts} placement="left">
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
                    name="slackAlerts"
                    color="primary"
                  />
                )}
                label=""
              />
            </Grid>
            <Grid item xs={4}>
              <Grid container direction="row" justifyContent="flex-end" alignItems="center">
                <SendTestSlackButton
                  disabled={Object.keys(errors).length !== 0}
                  botToken={values.bot_token}
                  botChannelId={values.bot_channel_id}
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

SlackForm.propTypes = {
  errors: PropTypes.shape({
    channel_name: PropTypes.string,
    bot_token: PropTypes.string,
    app_token: PropTypes.string,
    bot_channel_id: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    channel_name: PropTypes.string.isRequired,
    bot_token: PropTypes.string.isRequired,
    app_token: PropTypes.string.isRequired,
    bot_channel_id: PropTypes.string.isRequired,
    info: PropTypes.bool.isRequired,
    warning: PropTypes.bool.isRequired,
    critical: PropTypes.bool.isRequired,
    error: PropTypes.bool.isRequired,
    alerts: PropTypes.bool.isRequired,
    commands: PropTypes.bool.isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
  setFieldValue: PropTypes.func.isRequired,
};

export default SlackForm;
