import React from 'react';
import PropTypes from 'prop-types';
import {
  Box,
  Typography,
  FormControlLabel,
  Checkbox,
  Grid,
  Tooltip,
  InputAdornment,
} from '@material-ui/core';
import Button from 'components/material_ui/CustomButtons/Button';
import Divider from '@material-ui/core/Divider';
import InfoIcon from '@material-ui/icons/Info';
import { MuiThemeProvider } from '@material-ui/core/styles';
import { SendTestPagerDutyButton } from 'utils/buttons';
import { defaultTheme, theme } from 'components/theme/default';
import CssTextField from 'assets/jss/custom-jss/CssTextField';
import Data from 'data/channels';

let isDirty = false;

const PagerDutyForm = ({
  errors, values, handleSubmit, handleChange, dirty, toggleDirtyForm,
}) => {
  if (dirty !== isDirty) {
    isDirty = dirty;
    toggleDirtyForm({ isDirty });
  }

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
              {Data.pagerDuty.description}
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
                  placeholder={Data.pagerDuty.channelNamePlaceholder}
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
                          <Tooltip title={Data.pagerDuty.name} placement="left">
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
                  id="api-token-outlined-full-width"
                  error={!!(errors.api_token)}
                  value={values.api_token}
                  label="API Token"
                  type="text"
                  style={{ margin: 8 }}
                  name="api_token"
                  placeholder={Data.pagerDuty.apiTokenPlaceholder}
                  helperText={errors.api_token ? errors.api_token : ''}
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
                          <Tooltip title={Data.pagerDuty.token} placement="left">
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
                  id="integration-key-outlined-full-width"
                  error={!!(errors.integration_key)}
                  value={values.integration_key}
                  label="Integration Key"
                  type="text"
                  style={{ margin: 8 }}
                  name="integration_key"
                  placeholder={Data.pagerDuty.integrationKeyPlaceholder}
                  helperText={errors.integration_key ? errors.integration_key : ''}
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
                          <Tooltip title={Data.pagerDuty.integration_key} placement="left">
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
                    <Typography variant="subtitle1">
                      Severities
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={5}>
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
                        <Tooltip title={Data.pagerDuty.severities} placement="left">
                          <InfoIcon />
                        </Tooltip>
                      </MuiThemeProvider>
                    </Box>
                  </Grid>
                </Grid>
                <Grid item xs={4}>
                  <Grid container direction="row" justifyContent="flex-end" alignItems="center">
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
                  </Grid>
                </Grid>
              </Grid>
            </Grid>
          </Box>
        </form>
      </div>
    </MuiThemeProvider>
  );
};

PagerDutyForm.propTypes = {
  errors: PropTypes.shape({
    channel_name: PropTypes.string,
    api_token: PropTypes.string,
    integration_key: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  toggleDirtyForm: PropTypes.func.isRequired,
  dirty: PropTypes.bool.isRequired,
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
