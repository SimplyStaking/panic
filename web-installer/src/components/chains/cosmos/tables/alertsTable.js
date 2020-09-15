import React from 'react';
import PropTypes from 'prop-types';
import { makeStyles } from '@material-ui/core/styles';
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  FormControlLabel, Checkbox, Typography, MenuItem, FormControl,
  Select, TextField, Grid, Box,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import StepButtonContainer from '../../../../containers/chains/cosmos/stepButtonContainer';
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
    updateWarningDelay,
    updateWarningRepeat,
    updateWarningThreshold,
    updateWarningTimeWindow,
    updateWarningEnabled,
    updateCriticalDelay,
    updateCriticalRepeat,
    updateCriticalThreshold,
    updateCriticalTimeWindow,
    updateCriticalEnabled,
    updateAlertEnabled,
    updateAlertSeverityLevel,
    updateAlertSeverityEnabled,
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
      <Typography>
        Alert Threshold Configuration
      </Typography>
      <TableContainer component={Paper}>
        <Table className={classes.table} aria-label="simple table">
          <TableHead>
            <TableRow>
              <TableCell>Alert</TableCell>
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
                          updateWarningEnabled(
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
                          updateWarningDelay(
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
                          updateWarningRepeat(
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
                          updateWarningThreshold(
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
                          updateWarningTimeWindow(
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
                          updateCriticalEnabled(
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
                          updateCriticalDelay(
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
                          updateCriticalRepeat(
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
                          updateCriticalThreshold(
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
                          updateCriticalTimeWindow(
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
                          updateAlertEnabled(
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
      <Typography>
        Alert Severties Configuration
      </Typography>
      <TableContainer component={Paper}>
        <Table className={classes.table} aria-label="simple table">
          <TableHead>
            <TableRow>
              <TableCell>Alert</TableCell>
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
                        updateAlertSeverityLevel(
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
                          updateAlertSeverityEnabled(
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
      <Grid item xs={8} />
      <Grid item xs={4}>
        <Grid container direction="row" justify="flex-end" alignItems="center">
          <Box px={2}>
            <StepButtonContainer
              disabled={false}
              text={BACK}
              navigation={CHANNELS_STEP}
            />
          </Box>
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
  updateWarningDelay: PropTypes.func.isRequired,
  updateWarningRepeat: PropTypes.func.isRequired,
  updateWarningThreshold: PropTypes.func.isRequired,
  updateWarningTimeWindow: PropTypes.func.isRequired,
  updateWarningEnabled: PropTypes.func.isRequired,
  updateCriticalDelay: PropTypes.func.isRequired,
  updateCriticalRepeat: PropTypes.func.isRequired,
  updateCriticalThreshold: PropTypes.func.isRequired,
  updateCriticalTimeWindow: PropTypes.func.isRequired,
  updateCriticalEnabled: PropTypes.func.isRequired,
  updateAlertEnabled: PropTypes.func.isRequired,
  updateAlertSeverityLevel: PropTypes.func.isRequired,
  updateAlertSeverityEnabled: PropTypes.func.isRequired,
  pageChanger: PropTypes.func.isRequired,
  stepChanger: PropTypes.func.isRequired,
  addConfiguration: PropTypes.func.isRequired,
  resetConfiguration: PropTypes.func.isRequired,
};

export default AlertsTable;
