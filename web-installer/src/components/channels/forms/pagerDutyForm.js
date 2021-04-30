import React from 'react';
import PropTypes from 'prop-types';
import {
  TextField,
  Box,
  Typography,
  FormControlLabel,
  Checkbox,
  Grid,
  Tooltip,
} from '@material-ui/core';
import Button from 'components/material_ui/CustomButtons/Button';
import Divider from '@material-ui/core/Divider';
import InfoIcon from '@material-ui/icons/Info';
import { MuiThemeProvider } from '@material-ui/core/styles';
import { SendTestPagerDutyButton } from 'utils/buttons';
import { defaultTheme, theme } from 'components/theme/default';
import Data from 'data/channels';

const PagerDutyForm = ({
  errors, values, handleSubmit, handleChange,
}) => (
  <MuiThemeProvider theme={defaultTheme}>
    <div>
      <Typography variant="subtitle1" gutterBottom className="greyBackground">
        <Box m={2} p={3}>
          <p>{Data.pagerDuty.description}</p>
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
                placeholder="pager-duty-1"
                helperText={errors.channel_name ? errors.channel_name : ''}
                onChange={handleChange}
                autoComplete="off"
                fullWidth
              />
            </Grid>
            <Grid item xs={1}>
              <Grid container justify="center">
                <MuiThemeProvider theme={theme}>
                  <Tooltip title={Data.pagerDuty.name} placement="left">
                    <InfoIcon />
                  </Tooltip>
                </MuiThemeProvider>
              </Grid>
            </Grid>
            <Grid item xs={2}>
              <Typography> API Token </Typography>
            </Grid>
            <Grid item xs={9}>
              <TextField
                error={errors.api_token}
                value={values.api_token}
                type="text"
                name="api_token"
                placeholder="_gaffLaV3zAPx2A3hMPp"
                helperText={errors.api_token ? errors.api_token : ''}
                onChange={handleChange}
                autoComplete="off"
                fullWidth
              />
            </Grid>
            <Grid item xs={1}>
              <Grid container justify="center">
                <MuiThemeProvider theme={theme}>
                  <Tooltip title={Data.pagerDuty.token} placement="left">
                    <InfoIcon />
                  </Tooltip>
                </MuiThemeProvider>
              </Grid>
            </Grid>
            <Grid item xs={2}>
              <Typography> Integration Key </Typography>
            </Grid>
            <Grid item xs={9}>
              <TextField
                error={errors.integration_key}
                value={values.integration_key}
                type="text"
                name="integration_key"
                placeholder="9ba187h1f52176l75131dl5hxr6fdb1c8"
                helperText={
                  errors.integration_key ? errors.integration_key : ''
                }
                onChange={handleChange}
                autoComplete="off"
                fullWidth
              />
            </Grid>
            <Grid item xs={1}>
              <Grid container justify="center">
                <MuiThemeProvider theme={theme}>
                  <Tooltip
                    title={Data.pagerDuty.integration_key}
                    placement="left"
                  >
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
                  <Tooltip title={Data.pagerDuty.severities} placement="left">
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
                  <SendTestPagerDutyButton
                    disabled={Object.keys(errors).length !== 0}
                    apiToken={values.api_token}
                    integrationKey={values.integration_key}
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

PagerDutyForm.propTypes = {
  errors: PropTypes.shape({
    channel_name: PropTypes.string,
    api_token: PropTypes.string,
    integration_key: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    channel_name: PropTypes.string.isRequired,
    api_token: PropTypes.string.isRequired,
    integration_key: PropTypes.string.isRequired,
    info: PropTypes.bool.isRequired,
    warning: PropTypes.bool.isRequired,
    critical: PropTypes.bool.isRequired,
    error: PropTypes.bool.isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
};

export default PagerDutyForm;
