import React from 'react';
import PropTypes from 'prop-types';
import { makeStyles } from '@material-ui/core/styles';
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  FormControlLabel, Checkbox, Typography, MenuItem, FormControl,
  Select, TextField, Grid, Box,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import StepButtonContainer from '../../../../containers/chains/substrate/stepButtonContainer';
import NavigationButton from '../../../global/navigationButton';
import {
  CHAINS_PAGE, DONE, BACK, CHANNELS_STEP, CHAINS_STEP,
} from '../../../../constants/constants';

const useStyles = makeStyles({
  table: {
    minWidth: 650,
  },
});

const AlertsTable = (props) => {
  const classes = useStyles();

  const {
    config,
    updateWarningDelaySubstrate,
    updateWarningRepeatSubstrate,
    updateWarningThresholdSubstrate,
    updateWarningTimeWindowSubstrate,
    updateWarningEnabledSubstrate,
    updateCriticalDelaySubstrate,
    updateCriticalRepeatSubstrate,
    updateCriticalThresholdSubstrate,
    updateCriticalTimeWindowSubstrate,
    updateCriticalEnabledSubstrate,
    updateAlertEnabledSubstrate,
    updateAlertSeverityLevelSubstrate,
    updateAlertSeverityEnabledSubstrate,
  } = props;

  const nextPage = (page) => {
    const {
      pageChanger, stepChanger, addConfiguration, resetConfiguration,
    } = props;

    const payload = {
      step: CHAINS_STEP,
    };

    stepChanger(payload);
    pageChanger({ page });
    addConfiguration();
    resetConfiguration();
  };

  return (
    <div>
      <Typography
        style={{ textAlign: 'center' }}
        variant="h5"
        align="center"
        gutterBottom
      >
        Alert Threshold Configuration
      </Typography>
      <Box py={4}>
        <TableContainer component={Paper}>
          <Table className={classes.table} aria-label="simple table">
            <TableHead>
              <TableRow>
                <TableCell align="center">Alert</TableCell>
                <TableCell align="center">Warning Threshold</TableCell>
                <TableCell align="center">Critical Threshold</TableCell>
                <TableCell align="center">Enabled</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.keys(config.alerts.thresholds).map((alert) => (
                <TableRow key={config.alerts.thresholds[alert].name}>
                  <TableCell align="center">
                    {config.alerts.thresholds[alert].name}
                  </TableCell>
                  <TableCell align="center">
                    <FormControlLabel
                      control={(
                        <Checkbox
                          checked={config.alerts.thresholds[alert].warning.enabled}
                          onClick={() => {
                            updateWarningEnabledSubstrate(
                              {
                                alertID: alert,
                                enabled: !config.alerts.thresholds[alert].warning.enabled,
                              },
                            );
                          }}
                          color="primary"
                        />
                      )}
                      label="Enabled"
                      labelPlacement="end"
                    />
                    {config.alerts.thresholds[alert].warning.hasOwnProperty('delay')
                      && (
                        <TextField
                          value={config.alerts.thresholds[alert].warning.delay}
                          type="text"
                          name="delayWarning"
                          label="Delay"
                          placeholder="60"
                          onChange={(event) => {
                            updateWarningDelaySubstrate(
                              {
                                alertID: alert,
                                delay: event.target.value,
                              },
                            );
                          }}
                          fullWidth
                        />
                      )}
                    {config.alerts.thresholds[alert].warning.hasOwnProperty('repeat')
                      && (
                        <TextField
                          value={config.alerts.thresholds[alert].warning.repeat}
                          type="text"
                          name="repeatWarning"
                          label="Repeat"
                          placeholder="60"
                          onChange={(event) => {
                            updateWarningRepeatSubstrate(
                              {
                                alertID: alert,
                                repeat: event.target.value,
                              },
                            );
                          }}
                          fullWidth
                        />
                      )}
                    {config.alerts.thresholds[alert].warning.hasOwnProperty('threshold')
                      && (
                        <TextField
                          value={config.alerts.thresholds[alert].warning.threshold}
                          type="text"
                          name="thresholdWarning"
                          label="Threshold"
                          placeholder="60"
                          onChange={(event) => {
                            updateWarningThresholdSubstrate(
                              {
                                alertID: alert,
                                threshold: event.target.value,
                              },
                            );
                          }}
                          fullWidth
                        />
                      )}
                    {config.alerts.thresholds[alert].warning.hasOwnProperty('timewindow')
                      && (
                        <TextField
                          value={config.alerts.thresholds[alert].warning.timewindow}
                          type="text"
                          label="Time Window"
                          name="timewindowWarning"
                          placeholder="60"
                          onChange={(event) => {
                            updateWarningTimeWindowSubstrate(
                              {
                                alertID: alert,
                                timewindow: event.target.value,
                              },
                            );
                          }}
                          fullWidth
                        />
                      )}
                  </TableCell>
                  <TableCell align="center">
                    <FormControlLabel
                      control={(
                        <Checkbox
                          checked={config.alerts.thresholds[alert].critical.enabled}
                          onClick={() => {
                            updateCriticalEnabledSubstrate(
                              {
                                alertID: alert,
                                enabled: !config.alerts.thresholds[alert].critical.enabled,
                              },
                            );
                          }}
                          color="primary"
                        />
                      )}
                      label="Enabled"
                      labelPlacement="end"
                    />
                    {config.alerts.thresholds[alert].critical.hasOwnProperty('delay')
                      && (
                        <TextField
                          value={config.alerts.thresholds[alert].critical.delay}
                          type="text"
                          name="delayCritical"
                          label="Delay"
                          placeholder="60"
                          onChange={(event) => {
                            updateCriticalDelaySubstrate(
                              {
                                alertID: alert,
                                delay: event.target.value,
                              },
                            );
                          }}
                          fullWidth
                        />
                      )}
                    {config.alerts.thresholds[alert].critical.hasOwnProperty('repeat')
                      && (
                        <TextField
                          value={config.alerts.thresholds[alert].critical.repeat}
                          type="text"
                          name="repeatCritical"
                          label="Repeat"
                          placeholder="60"
                          onChange={(event) => {
                            updateCriticalRepeatSubstrate(
                              {
                                alertID: alert,
                                repeat: event.target.value,
                              },
                            );
                          }}
                          fullWidth
                        />
                      )}
                    {config.alerts.thresholds[alert].critical.hasOwnProperty('threshold')
                      && (
                        <TextField
                          value={config.alerts.thresholds[alert].critical.threshold}
                          type="text"
                          name="thresholdCritical"
                          label="Threshold"
                          placeholder="60"
                          onChange={(event) => {
                            updateCriticalThresholdSubstrate(
                              {
                                alertID: alert,
                                threshold: event.target.value,
                              },
                            );
                          }}
                          fullWidth
                        />
                      )}
                    {config.alerts.thresholds[alert].critical.hasOwnProperty('timewindow')
                      && (
                        <TextField
                          value={config.alerts.thresholds[alert].critical.timewindow}
                          type="text"
                          label="Time Window"
                          name="timewindowCritical"
                          placeholder="60"
                          onChange={(event) => {
                            updateCriticalTimeWindowSubstrate(
                              {
                                alertID: alert,
                                timewindow: event.target.value,
                              },
                            );
                          }}
                          fullWidth
                        />
                      )}
                  </TableCell>
                  <TableCell align="center">
                    <FormControlLabel
                      control={(
                        <Checkbox
                          checked={config.alerts.thresholds[alert].enabled}
                          onClick={() => {
                            updateAlertEnabledSubstrate(
                              {
                                alertID: alert,
                                enabled: !config.alerts.thresholds[alert].enabled,
                              },
                            );
                          }}
                          name="enabled"
                          color="primary"
                        />
                      )}
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
      <Typography
        style={{ textAlign: 'center' }}
        variant="h5"
        align="center"
        gutterBottom
      >
        Alert Severties Configuration
      </Typography>
      <Box py={4}>
        <TableContainer component={Paper}>
          <Table className={classes.table} aria-label="simple table">
            <TableHead>
              <TableRow>
                <TableCell align="center">Alert</TableCell>
                <TableCell align="center">Severity</TableCell>
                <TableCell align="center">Enabled</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.keys(config.alerts.severties).map((alert) => (
                <TableRow key={config.alerts.severties[alert].name}>
                  <TableCell align="center">
                    {config.alerts.severties[alert].name}
                  </TableCell>
                  <TableCell align="center">
                    <FormControl className={classes.formControl}>
                      <Select
                        labelId="severity"
                        id="severity-selection"
                        value={config.alerts.severties[alert].severtiy}
                        onChange={(event) => {
                          updateAlertSeverityLevelSubstrate(
                            {
                              alertID: alert,
                              severtiy: event.target.value,
                            },
                          );
                        }}
                      >
                        <MenuItem value="INFO">Info</MenuItem>
                        <MenuItem value="WARNING">Warning</MenuItem>
                        <MenuItem value="CRITICAL">Critical</MenuItem>
                      </Select>
                    </FormControl>
                  </TableCell>
                  <TableCell align="center">
                    <FormControlLabel
                      control={(
                        <Checkbox
                          checked={config.alerts.severties[alert].enabled}
                          onClick={() => {
                            updateAlertSeverityEnabledSubstrate(
                              {
                                alertID: alert,
                                enabled: !config.alerts.severties[alert].enabled,
                              },
                            );
                          }}
                          name="enabled"
                          color="primary"
                        />
                      )}
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
      <Grid container spacing={2}>
        <Grid item xs={2}>
          <Box px={2}>
            <StepButtonContainer
              disabled={false}
              text={BACK}
              navigation={CHANNELS_STEP}
            />
          </Box>
        </Grid>
        <Grid item xs={8} />
        <Grid item xs={2}>
          <Box px={2}>
            <NavigationButton
              disabled={false}
              nextPage={nextPage}
              buttonText={DONE}
              navigation={CHAINS_PAGE}
            />
          </Box>
        </Grid>
      </Grid>
    </div>
  );
};

AlertsTable.propTypes = {
  updateWarningDelaySubstrate: PropTypes.func.isRequired,
  updateWarningRepeatSubstrate: PropTypes.func.isRequired,
  updateWarningThresholdSubstrate: PropTypes.func.isRequired,
  updateWarningTimeWindowSubstrate: PropTypes.func.isRequired,
  updateWarningEnabledSubstrate: PropTypes.func.isRequired,
  updateCriticalDelaySubstrate: PropTypes.func.isRequired,
  updateCriticalRepeatSubstrate: PropTypes.func.isRequired,
  updateCriticalThresholdSubstrate: PropTypes.func.isRequired,
  updateCriticalTimeWindowSubstrate: PropTypes.func.isRequired,
  updateCriticalEnabledSubstrate: PropTypes.func.isRequired,
  updateAlertEnabledSubstrate: PropTypes.func.isRequired,
  updateAlertSeverityLevelSubstrate: PropTypes.func.isRequired,
  updateAlertSeverityEnabledSubstrate: PropTypes.func.isRequired,
  pageChanger: PropTypes.func.isRequired,
  stepChanger: PropTypes.func.isRequired,
  addConfiguration: PropTypes.func.isRequired,
  resetConfiguration: PropTypes.func.isRequired,
};

export default AlertsTable;
