import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
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
import { SendTestOpsGenieButton } from 'utils/buttons';
import { defaultTheme, theme } from 'components/theme/default';
import Data from 'data/channels';

const OpsGenieForm = ({
  errors, values, handleSubmit, handleChange,
}) => (
  <MuiThemeProvider theme={defaultTheme}>
    <div>
      <Typography variant="subtitle1" gutterBottom className="greyBackground">
        <Box m={2} p={3}>
          <p>{Data.opsGenie.description}</p>
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
                placeholder="ops-genie-1"
                helperText={errors.channel_name ? errors.channel_name : ''}
                onChange={handleChange}
                autoComplete="off"
                fullWidth
              />
            </Grid>
            <Grid item xs={1}>
              <Grid container justify="center">
                <MuiThemeProvider theme={theme}>
                  <Tooltip title={Data.opsGenie.name} placement="left">
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
                placeholder="0a9sjd09j1md00d10md19mda2a"
                helperText={errors.api_token ? errors.api_token : ''}
                onChange={handleChange}
                autoComplete="off"
                fullWidth
              />
            </Grid>
            <Grid item xs={1}>
              <Grid container justify="center">
                <MuiThemeProvider theme={theme}>
                  <Tooltip title={Data.opsGenie.token} placement="left">
                    <InfoIcon />
                  </Tooltip>
                </MuiThemeProvider>
              </Grid>
            </Grid>
            <Grid item xs={2}>
              <Typography> EU </Typography>
            </Grid>
            <Grid item xs={1}>
              <FormControlLabel
                control={(
                  <Checkbox
                    checked={values.eu}
                    onChange={handleChange}
                    name="eu"
                    color="primary"
                  />
                  )}
                label=""
              />
            </Grid>
            <Grid item xs={8} />
            <Grid item xs={1}>
              <Grid container justify="center">
                <MuiThemeProvider theme={theme}>
                  <Tooltip title={Data.opsGenie.eu} placement="left">
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
                  <Tooltip title={Data.opsGenie.severities} placement="left">
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
                  <SendTestOpsGenieButton
                    disabled={Object.keys(errors).length !== 0}
                    apiKey={values.api_token}
                    eu={values.eu}
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

OpsGenieForm.propTypes = forbidExtraProps({
  errors: PropTypes.shape({
    channel_name: PropTypes.string,
    api_token: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    channel_name: PropTypes.string.isRequired,
    api_token: PropTypes.string.isRequired,
    eu: PropTypes.bool.isRequired,
    info: PropTypes.bool.isRequired,
    warning: PropTypes.bool.isRequired,
    critical: PropTypes.bool.isRequired,
    error: PropTypes.bool.isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
});

export default OpsGenieForm;
