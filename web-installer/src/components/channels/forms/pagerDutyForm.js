import React from 'react';
import PropTypes from 'prop-types';
import {
  TextField, Button, Box, Typography, FormControlLabel, Checkbox, Grid, Tooltip,
} from '@material-ui/core';
import Divider from '@material-ui/core/Divider';
import InfoIcon from '@material-ui/icons/Info';
import { MuiThemeProvider } from '@material-ui/core/styles';
import { SendTestPagerDutyButton } from '../../../utils/buttons';
import { defaultTheme, theme, useStyles } from '../../theme/default';
import Data from '../../../data/channels';

const PagerDutyForm = (props) => {
  const classes = useStyles();

  const {
    errors,
    values,
    handleSubmit,
    handleChange,
  } = props;

  return (
    <MuiThemeProvider theme={defaultTheme}>
      <div>
        <Typography variant="subtitle1" gutterBottom className="greyBackground">
          <Box m={2} p={3}>
            <p>{Data.pagerDuty.description}</p>
          </Box>
        </Typography>
        <Divider />
        <form onSubmit={handleSubmit} className={classes.root}>
          <Box p={3}>
            <Grid container spacing={3} justify="center" alignItems="center">
              <Grid item xs={2}>
                <Typography> Configuration Name: </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  error={errors.configName}
                  value={values.configName}
                  type="text"
                  name="configName"
                  placeholder="pager-duty-1"
                  helperText={errors.configName ? errors.configName : ''}
                  onChange={handleChange}
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
                <Typography> API Token: </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  error={errors.apiToken}
                  value={values.apiToken}
                  type="text"
                  name="apiToken"
                  placeholder="_xaegfLaV3zAPx2A3hMPp"
                  helperText={errors.apiToken ? errors.apiToken : ''}
                  onChange={handleChange}
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
                <Typography> Integration Key: </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  error={errors.integrationKey}
                  value={values.integrationKey}
                  type="text"
                  name="integrationKey"
                  placeholder="9ba187h1f52176l75131dl5hxr6fdb1c8"
                  helperText={errors.integrationKey ? errors.integrationKey : ''}
                  onChange={handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={Data.pagerDuty.integrationKey} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={2}>
                <Typography> Severities: </Typography>
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
                    <Tooltip title={Data.pagerDuty.severties} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={8} />
              <Grid item xs={4}>
                <Grid container direction="row" justify="flex-end" alignItems="center">
                  <Box px={2}>
                    <SendTestPagerDutyButton
                      disabled={(Object.keys(errors).length !== 0)}
                      apiToken={values.apiToken}
                      integrationKey={values.integrationKey}
                    />
                    <Button
                      variant="outlined"
                      size="large"
                      disabled={(Object.keys(errors).length !== 0)}
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
          </Box>
        </form>
      </div>
    </MuiThemeProvider>
  );
};

PagerDutyForm.propTypes = {
  errors: PropTypes.shape({
    configName: PropTypes.string,
    apiToken: PropTypes.string,
    integrationKey: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    configName: PropTypes.string.isRequired,
    apiToken: PropTypes.string.isRequired,
    integrationKey: PropTypes.string.isRequired,
    info: PropTypes.bool.isRequired,
    warning: PropTypes.bool.isRequired,
    critical: PropTypes.bool.isRequired,
    error: PropTypes.bool.isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
};

export default PagerDutyForm;
