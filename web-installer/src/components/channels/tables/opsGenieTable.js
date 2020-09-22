import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Button,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import CheckIcon from '@material-ui/icons/Check';
import ClearIcon from '@material-ui/icons/Clear';
import CancelIcon from '@material-ui/icons/Cancel';

const OpsGenieTable = (props) => {
  const {
    opsGenies,
    removeOpsGenieDetails,
  } = props;

  if (opsGenies.length === 0) {
    return <div />;
  }
  return (
    <TableContainer component={Paper}>
      <Table className="greyBackground" aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell align="center">Name</TableCell>
            <TableCell align="center">API Token</TableCell>
            <TableCell align="center">Info</TableCell>
            <TableCell align="center">Warning</TableCell>
            <TableCell align="center">Critical</TableCell>
            <TableCell align="center">Error</TableCell>
            <TableCell align="center">Delete</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {opsGenies.map((opsGenie) => (
            <TableRow key={opsGenie.configName}>
              <TableCell component="th" scope="row">
                {opsGenie.configName}
              </TableCell>
              <TableCell align="center">{opsGenie.apiToken}</TableCell>
              <TableCell align="center">
                {opsGenie.info ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                {opsGenie.warning ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                {opsGenie.critical ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                {opsGenie.error ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                <Button onClick={() => { removeOpsGenieDetails(opsGenie); }}>
                  <CancelIcon />
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

OpsGenieTable.propTypes = forbidExtraProps({
  opsGenies: PropTypes.arrayOf(PropTypes.shape({
    configName: PropTypes.string.isRequired,
    apiToken: PropTypes.string.isRequired,
    info: PropTypes.bool.isRequired,
    warning: PropTypes.bool.isRequired,
    critical: PropTypes.bool.isRequired,
    error: PropTypes.bool.isRequired,
  })).isRequired,
  removeOpsGenieDetails: PropTypes.func.isRequired,
});

export default OpsGenieTable;
