import React from 'react';
import PropTypes from 'prop-types';
import { makeStyles } from '@material-ui/core/styles';
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  FormControlLabel, Checkbox, Typography, MenuItem, FormControl,
  Select, TextField,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';

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
  } = props;

  const handleChange = (event) => {
    console.log(event.target.value);
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
                        color="primary"
                      />
                    )}
                    label="Enabled"
                    labelPlacement="end"
                  />
                  {config.alerts.thresholds[alert].warning.hasOwnProperty('delay')
                    && (
                      <div>
                        <p>
                          Delay:
                          {' '}
                        </p>
                        <TextField
                          value={config.alerts.thresholds[alert].warning.delay}
                          type="text"
                          name="delayWarning"
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
                      </div>
                    )}
                  {config.alerts.thresholds[alert].warning.hasOwnProperty('repeat')
                    && (
                      <div>
                        <p>
                          Repeat:
                          {' '}
                        </p>
                        <TextField
                          value={config.alerts.thresholds[alert].warning.repeat}
                          type="text"
                          name="repeatWarning"
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
                      </div>
                    )}
                  {config.alerts.thresholds[alert].warning.hasOwnProperty('threshold')
                    && (
                      <div>
                        <p>
                          Threshold:
                          {' '}
                        </p>
                        <TextField
                          value={config.alerts.thresholds[alert].warning.threshold}
                          type="text"
                          name="thresholdWarning"
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
                      </div>
                    )}
                  {config.alerts.thresholds[alert].warning.hasOwnProperty('timewindow')
                    && (
                      <div>
                        <p>
                          Time Window:
                          {' '}
                        </p>
                        <TextField
                          value={config.alerts.thresholds[alert].warning.timewindow}
                          type="text"
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
                      </div>
                    )}
                </TableCell>
                <TableCell align="center">
                  {/* <FormControlLabel
                    control={(
                      <Checkbox
                        checked={alert.critical.enabled}
                        color="primary"
                      />
                    )}
                    label="Enabled:"
                    labelPlacement="end"
                  />
                  {alert.critical.hasOwnProperty('delay')
                    && (
                    <p>
                      Delay:
                      {' '}
                      {alert.critical.delay}
                    </p>
                    )}
                  {alert.critical.hasOwnProperty('repeat')
                    && (
                    <p>
                      Repeat:
                      {' '}
                      {alert.critical.repeat}
                    </p>
                    )}
                  {alert.critical.hasOwnProperty('threshold')
                    && (
                    <p>
                      Threshold:
                      {' '}
                      {alert.critical.threshold}
                    </p>
                    )}
                  {alert.critical.hasOwnProperty('timewindow')
                    && (
                    <p>
                      Time Window:
                      {' '}
                      {alert.critical.timewindow}
                    </p>
                    )} */}
                </TableCell>
                <TableCell align="center">
                  {/* <FormControlLabel
                    control={(
                      <Checkbox
                        checked={alert.enabled}
                        name="enabled"
                        color="primary"
                      />
                    )}
                  /> */}
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
            {config.alerts.severties.map((alert) => (
              <TableRow key={alert.name}>
                <TableCell align="center">
                  {alert.name}
                </TableCell>
                <TableCell align="center">
                  <FormControl className={classes.formControl}>
                    <Select
                      labelId="severity"
                      id="severity-selection"
                      value={alert.severtiy}
                      onChange={handleChange}
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
                        checked={alert.enabled}
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
    </div>
  );
};

AlertsTable.propTypes = {
  // config: PropTypes.shape({
  //   alerts: PropTypes.arrayOf(PropTypes.shape({
  //     thresholds: 
  //     cosmosNodeName: PropTypes.string.isRequired,
  //     tendermintRPCURL: PropTypes.string.isRequired,
  //     cosmosRPCURL: PropTypes.string.isRequired,
  //     prometheusURL: PropTypes.string.isRequired,
  //     exporterURL: PropTypes.string.isRequired,
  //     isValidator: PropTypes.bool.isRequired,
  //     monitorNode: PropTypes.bool.isRequired,
  //     isArchiveNode: PropTypes.bool.isRequired,
  //     useAsDataSource: PropTypes.bool.isRequired,
  //   })).isRequired,
  // }).isRequired,
  updateWarningDelay: PropTypes.func.isRequired,
  updateWarningRepeat: PropTypes.func.isRequired,
  updateWarningThreshold: PropTypes.func.isRequired,
  updateWarningTimeWindow: PropTypes.func.isRequired,
  updateWarningEnabled: PropTypes.func.isRequired,
};

export default AlertsTable;
