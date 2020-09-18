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

const PagerDutyTable = (props) => {

  const {
    pagerDuties,
    removePagerDutyDetails,
  } = props;

  if (pagerDuties.length === 0) {
    return <div />;
  }
  return (
    <TableContainer component={Paper}>
      <Table className="greyBackground" aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell align="center">PagerDuty Name</TableCell>
            <TableCell align="center">API Token</TableCell>
            <TableCell align="center">Integration Key</TableCell>
            <TableCell align="center">Info</TableCell>
            <TableCell align="center">Warning</TableCell>
            <TableCell align="center">Critical</TableCell>
            <TableCell align="center">Error</TableCell>
            <TableCell align="center">Delete</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {pagerDuties.map((pagerDuty) => (
            <TableRow key={pagerDuty.configName}>
              <TableCell component="th" scope="row">
                {pagerDuty.configName}
              </TableCell>
              <TableCell align="center">{pagerDuty.apiToken}</TableCell>
              <TableCell align="center">{pagerDuty.integrationKey}</TableCell>
              <TableCell align="center">
                {pagerDuty.info ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                {pagerDuty.warning ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                {pagerDuty.critical ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                {pagerDuty.error ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                <Button onClick={() => { removePagerDutyDetails(pagerDuty); }}>
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

PagerDutyTable.propTypes = forbidExtraProps({
  pagerDuties: PropTypes.arrayOf(PropTypes.shape({
    configName: PropTypes.string.isRequired,
    apiToken: PropTypes.string.isRequired,
    integrationKey: PropTypes.string.isRequired,
    info: PropTypes.bool.isRequired,
    warning: PropTypes.bool.isRequired,
    critical: PropTypes.bool.isRequired,
    error: PropTypes.bool.isRequired,
  })).isRequired,
  removePagerDutyDetails: PropTypes.func.isRequired,
});

export default PagerDutyTable;
