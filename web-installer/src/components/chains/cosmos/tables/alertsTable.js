import React from 'react';
import PropTypes from 'prop-types';
import { makeStyles } from '@material-ui/core/styles';
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Button, FormControlLabel, Checkbox, Typography,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import CheckIcon from '@material-ui/icons/Check';
import ClearIcon from '@material-ui/icons/Clear';
import CancelIcon from '@material-ui/icons/Cancel';

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
                        // checked={config.telegrams.includes(telegram.botName)}
                        // onClick={() => {
                        //   if (config.telegrams.includes(telegram.botName)) {
                        //     removeTelegramDetails(telegram.botName);
                        //   } else {
                        //     addTelegramDetails(telegram.botName);
                        //   }
                        // }}
                        // name="telegrams"
                        color="primary"
                      />
                    )}
                  />
                </TableCell>
              </TableRow>
            ))}
            <TableRow>
              <TableCell>

              </TableCell>
            </TableRow>
            {/* {config.nodes.map((node) => (
              <TableRow key={node.cosmosNodeName}>
                <TableCell component="th" scope="row">
                  {node.cosmosNodeName}
                </TableCell>
                <TableCell align="center">{node.tendermintRPCURL}</TableCell>
                <TableCell align="center">{node.cosmosRPCURL}</TableCell>
                <TableCell align="center">{node.prometheusURL}</TableCell>
                <TableCell align="center">{node.exporterURL}</TableCell>
                <TableCell align="center">
                  {node.isValidator ? <CheckIcon /> : <ClearIcon />}
                </TableCell>
                <TableCell align="center">
                  {node.monitorNode ? <CheckIcon /> : <ClearIcon />}
                </TableCell>
                <TableCell align="center">
                  {node.isArchiveNode ? <CheckIcon /> : <ClearIcon />}
                </TableCell>
                <TableCell align="center">
                  {node.useAsDataSource ? <CheckIcon /> : <ClearIcon />}
                </TableCell>
                <TableCell align="center">
                  <Button onClick={() => { }}>
                    <CancelIcon />
                  </Button>
                </TableCell>
              </TableRow>
            ))} */}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
};

AlertsTable.propTypes = {
  config: PropTypes.shape({
    nodes: PropTypes.arrayOf(PropTypes.shape({
      cosmosNodeName: PropTypes.string.isRequired,
      tendermintRPCURL: PropTypes.string.isRequired,
      cosmosRPCURL: PropTypes.string.isRequired,
      prometheusURL: PropTypes.string.isRequired,
      exporterURL: PropTypes.string.isRequired,
      isValidator: PropTypes.bool.isRequired,
      monitorNode: PropTypes.bool.isRequired,
      isArchiveNode: PropTypes.bool.isRequired,
      useAsDataSource: PropTypes.bool.isRequired,
    })).isRequired,
  }).isRequired,
};

export default AlertsTable;
