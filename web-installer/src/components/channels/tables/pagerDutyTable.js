import React from 'react';
import PropTypes from 'prop-types';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import CheckIcon from '@material-ui/icons/Check';
import ClearIcon from '@material-ui/icons/Clear';
import CancelIcon from '@material-ui/icons/Cancel';

const PagerDutyTable = ({ pagerDuties, removePagerDutyDetails }) => {
  if (pagerDuties.allIds.length === 0) {
    return <div />;
  }
  return (
    <TableContainer component={Paper}>
      <Table className="greyBackground" aria-label="pagerduties table">
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
          {Object.keys(pagerDuties.byId).map((pagerDuty) => (
            <TableRow key={pagerDuties.byId[pagerDuty].id}>
              <TableCell align="center">
                {pagerDuties.byId[pagerDuty].channel_name}
              </TableCell>
              <TableCell align="center">
                {pagerDuties.byId[pagerDuty].api_token}
              </TableCell>
              <TableCell align="center">
                {pagerDuties.byId[pagerDuty].integration_key}
              </TableCell>
              <TableCell align="center">
                {pagerDuties.byId[pagerDuty].info ? (
                  <CheckIcon />
                ) : (
                  <ClearIcon />
                )}
              </TableCell>
              <TableCell align="center">
                {pagerDuties.byId[pagerDuty].warning ? (
                  <CheckIcon />
                ) : (
                  <ClearIcon />
                )}
              </TableCell>
              <TableCell align="center">
                {pagerDuties.byId[pagerDuty].critical ? (
                  <CheckIcon />
                ) : (
                  <ClearIcon />
                )}
              </TableCell>
              <TableCell align="center">
                {pagerDuties.byId[pagerDuty].error ? (
                  <CheckIcon />
                ) : (
                  <ClearIcon />
                )}
              </TableCell>
              <TableCell align="center">
                <Button
                  onClick={() => {
                    removePagerDutyDetails(pagerDuties.byId[pagerDuty]);
                  }}
                >
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

PagerDutyTable.propTypes = {
  pagerDuties: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      channel_name: PropTypes.string,
      api_token: PropTypes.string,
      integration_key: PropTypes.string,
      info: PropTypes.bool,
      warning: PropTypes.bool,
      critical: PropTypes.bool,
      error: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  removePagerDutyDetails: PropTypes.func.isRequired,
};

export default PagerDutyTable;
