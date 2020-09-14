import React from 'react';
import PropTypes from 'prop-types';
import { makeStyles } from '@material-ui/core/styles';
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  FormControlLabel, Checkbox, Typography, MenuItem, FormControl,
  Select,
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
            {config.alerts.thresholds.map((alert) => (
              <TableRow key={alert.name}>
                <TableCell align="center">
                  {alert.name}
                </TableCell>
                <TableCell align="center">
                  <FormControlLabel
                    control={(
                      <Checkbox
                        checked={alert.warning.enabled}
                        color="primary"
                      />
                    )}
                    label="Enabled"
                    labelPlacement="end"
                  />
                  {alert.warning.hasOwnProperty('delay')
                    && (
                    <p>
                      Delay:
                      {' '}
                      {alert.warning.delay}
                    </p>
                    )}
                  {alert.warning.hasOwnProperty('repeat')
                    && (
                    <p>
                      Repeat:
                      {' '}
                      {alert.warning.repeat}
                    </p>
                    )}
                  {alert.warning.hasOwnProperty('threshold')
                    && (
                    <p>
                      Threshold:
                      {' '}
                      {alert.warning.threshold}
                    </p>
                    )}
                  {alert.warning.hasOwnProperty('timewindow')
                    && (
                    <p>
                      Time Window:
                      {' '}
                        {alert.warning.timewindow}
                    </p>
                    )}
                </TableCell>
                <TableCell align="center">
                  <FormControlLabel
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
                    )}
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
};

export default AlertsTable;
