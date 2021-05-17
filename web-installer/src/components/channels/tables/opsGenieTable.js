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

const OpsGenieTable = ({ opsGenies, removeOpsGenieDetails }) => {
  if (opsGenies.allIds.length === 0) {
    return <div />;
  }
  return (
    <Box pt={8}>
      <TableContainer component={Paper}>
        <Table className="greyBackground" aria-label="opsgenie-table">
          <TableHead>
            <TableRow>
              <StyledTableCell align="center">Name</StyledTableCell>
              <StyledTableCell align="center">API Token</StyledTableCell>
              <StyledTableCell align="center">EU</StyledTableCell>
              <StyledTableCell align="center">Info</StyledTableCell>
              <StyledTableCell align="center">Warning</StyledTableCell>
              <StyledTableCell align="center">Critical</StyledTableCell>
              <StyledTableCell align="center">Error</StyledTableCell>
              <StyledTableCell align="center">Delete</StyledTableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {Object.keys(opsGenies.byId).map((opsgenie) => (
              <StyledTableRow key={opsGenies.byId[opsgenie].id}>
                <StyledTableCell align="center">
                  {opsGenies.byId[opsgenie].channel_name}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {opsGenies.byId[opsgenie].api_token}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {opsGenies.byId[opsgenie].eu ? <CheckIcon /> : <ClearIcon />}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {opsGenies.byId[opsgenie].info ? <CheckIcon /> : <ClearIcon />}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {opsGenies.byId[opsgenie].warning ? (
                    <CheckIcon />
                  ) : (
                    <ClearIcon />
                  )}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {opsGenies.byId[opsgenie].critical ? (
                    <CheckIcon />
                  ) : (
                    <ClearIcon />
                  )}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {opsGenies.byId[opsgenie].error ? <CheckIcon /> : <ClearIcon />}
                </StyledTableCell>
                <StyledTableCell align="center">
                  <Button
                    onClick={() => {
                      removeOpsGenieDetails(opsGenies.byId[opsgenie]);
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

OpsGenieTable.propTypes = {
  opsGenies: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      channel_name: PropTypes.string,
      api_token: PropTypes.string,
      eu: PropTypes.bool,
      info: PropTypes.bool,
      warning: PropTypes.bool,
      critical: PropTypes.bool,
      error: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  removeOpsGenieDetails: PropTypes.func.isRequired,
};

export default OpsGenieTable;
