import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import {
  TextField,
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
import Data from 'data/channels';

const SlackForm = ({
  errors,
  values,
  handleSubmit,
  handleChange,
  setFieldValue,
}) => (
  <MuiThemeProvider theme={defaultTheme}>
    <div>
      <Typography variant="subtitle1" gutterBottom className="greyBackground">
        <Box m={2} p={3}>
          <p>{Data.slack.description}</p>
        </Box>
      </Typography>
      <Divider />
      <form onSubmit={handleSubmit} className="root">
        <Box p={3}>
          <Grid container spacing={3} justify="center" alignItems="center">
            <Grid item xs={2}>
              <Typography> Name </Typography>
            </Grid>
            <Grid item xs={9}>
              <TextField
                error={errors.channel_name}
                value={values.channel_name}
                type="text"
                name="channel_name"
                placeholder={Data.slack.channel_namePlaceholder}
                helperText={errors.channel_name ? errors.channel_name : ''}
                onChange={handleChange}
                autoComplete="off"
                fullWidth
              />
            </Grid>
            <Grid item xs={1}>
              <Grid container justify="center">
                <MuiThemeProvider theme={theme}>
                  <Tooltip title={Data.slack.name} placement="left">
                    <InfoIcon />
                  </Tooltip>
                </MuiThemeProvider>
              </Grid>
            </Grid>
            <Grid item xs={2}>
              <Typography> Token </Typography>
            </Grid>
            <Grid item xs={9}>
              <TextField
                error={errors.token}
                value={values.token}
                type="text"
                name="token"
                placeholder={Data.slack.tokenPlaceholder}
                helperText={errors.token ? errors.token : ''}
                onChange={handleChange}
                autoComplete="off"
                fullWidth
              />
            </Grid>
            <Grid item xs={1}>
              <Grid container justify="center">
                <MuiThemeProvider theme={theme}>
                  <Tooltip title={Data.slack.token} placement="left">
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
                  <Tooltip title={Data.slack.severities} placement="left">
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
              <Typography> Telegram Alerts </Typography>
            </Grid>
            <Grid item xs={1}>
              <Grid container justify="center">
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
              <Grid
                container
                direction="row"
                justify="flex-end"
                alignItems="center"
              >
                <Box px={2}>
                  <SendTestSlackButton
                    disabled={Object.keys(errors).length !== 0}
                    chatID={values.chat_id}
                    token={values.token}
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

SlackForm.propTypes = forbidExtraProps({
  errors: PropTypes.shape({
    channel_name: PropTypes.string,
    chat_id: PropTypes.string,
    token: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    channel_name: PropTypes.string.isRequired,
    chat_id: PropTypes.string.isRequired,
    token: PropTypes.string.isRequired,
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

export default SlackForm;
