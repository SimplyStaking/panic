import React from 'react';
import PropTypes from 'prop-types';
import {
  Table,
  TableBody,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Box,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import CheckIcon from '@material-ui/icons/Check';
import ClearIcon from '@material-ui/icons/Clear';
import CancelIcon from '@material-ui/icons/Cancel';
import StyledTableRow from 'assets/jss/custom-jss/StyledTableRow';
import StyledTableCell from 'assets/jss/custom-jss/StyledTableCell';

const PagerDutyTable = ({ pagerDuties, removePagerDutyDetails }) => {
  if (pagerDuties.allIds.length === 0) {
    return <div />;
  }
  return (
    <Box pt={8}>
      <TableContainer component={Paper}>
        <Table className="greyBackground" aria-label="pagerduty table">
          <TableHead>
            <TableRow>
              <StyledTableCell align="center">PagerDuty Name</StyledTableCell>
              <StyledTableCell align="center">API Token</StyledTableCell>
              <StyledTableCell align="center">Integration Key</StyledTableCell>
              <StyledTableCell align="center">Info</StyledTableCell>
              <StyledTableCell align="center">Warning</StyledTableCell>
              <StyledTableCell align="center">Critical</StyledTableCell>
              <StyledTableCell align="center">Error</StyledTableCell>
              <StyledTableCell align="center">Delete</StyledTableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {Object.keys(pagerDuties.byId).map((pagerDuty) => (
              <StyledTableRow key={pagerDuties.byId[pagerDuty].id}>
                <StyledTableCell align="center">
                  {pagerDuties.byId[pagerDuty].channel_name}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {pagerDuties.byId[pagerDuty].api_token}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {pagerDuties.byId[pagerDuty].integration_key}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {pagerDuties.byId[pagerDuty].info ? (
                    <CheckIcon />
                  ) : (
                    <ClearIcon />
                  )}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {pagerDuties.byId[pagerDuty].warning ? (
                    <CheckIcon />
                  ) : (
                    <ClearIcon />
                  )}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {pagerDuties.byId[pagerDuty].critical ? (
                    <CheckIcon />
                  ) : (
                    <ClearIcon />
                  )}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {pagerDuties.byId[pagerDuty].error ? (
                    <CheckIcon />
                  ) : (
                    <ClearIcon />
                  )}
                </StyledTableCell>
                <StyledTableCell align="center">
                  <Button
                    onClick={() => {
                      removePagerDutyDetails(pagerDuties.byId[pagerDuty]);
                    }}
                  >
                    <CancelIcon />
                  </Button>
                </StyledTableCell>
              </StyledTableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
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
