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

const SlackTable = ({ slacks, removeSlackDetails }) => {
  if (slacks.allIds.length === 0) {
    return <div />;
  }
  return (
    <Box pt={8}>
      <TableContainer component={Paper}>
        <Table className="greyBackground" aria-label="simple table">
          <TableHead>
            <TableRow>
              <StyledTableCell align="center">Slack Name</StyledTableCell>
              <StyledTableCell align="center">Bot Token</StyledTableCell>
              <StyledTableCell align="center">Bot Channel Name</StyledTableCell>
              <StyledTableCell align="center">Info</StyledTableCell>
              <StyledTableCell align="center">Warning</StyledTableCell>
              <StyledTableCell align="center">Critical</StyledTableCell>
              <StyledTableCell align="center">Error</StyledTableCell>
              <StyledTableCell align="center">Alerts</StyledTableCell>
              <StyledTableCell align="center">Commands</StyledTableCell>
              <StyledTableCell align="center">Delete</StyledTableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {Object.keys(slacks.byId).map((slack) => (
              <StyledTableRow key={slacks.byId[slack].id}>
                <StyledTableCell align="center">
                  {slacks.byId[slack].channel_name}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {slacks.byId[slack].bot_token}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {slacks.byId[slack].app_token}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {slacks.byId[slack].bot_channel_id}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {slacks.byId[slack].info ? (
                    <CheckIcon />
                  ) : (
                    <ClearIcon />
                  )}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {slacks.byId[slack].warning ? (
                    <CheckIcon />
                  ) : (
                    <ClearIcon />
                  )}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {slacks.byId[slack].critical ? (
                    <CheckIcon />
                  ) : (
                    <ClearIcon />
                  )}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {slacks.byId[slack].error ? (
                    <CheckIcon />
                  ) : (
                    <ClearIcon />
                  )}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {slacks.byId[slack].alerts ? (
                    <CheckIcon />
                  ) : (
                    <ClearIcon />
                  )}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {slacks.byId[slack].commands ? (
                    <CheckIcon />
                  ) : (
                    <ClearIcon />
                  )}
                </StyledTableCell>
                <StyledTableCell align="center">
                  <Button
                    onClick={() => {
                      removeSlackDetails(slacks.byId[slack]);
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

SlackTable.propTypes = {
  slacks: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      channel_name: PropTypes.string,
      bot_token: PropTypes.string,
      app_token: PropTypes.string,
      bot_channel_id: PropTypes.string,
      info: PropTypes.bool,
      warning: PropTypes.bool,
      critical: PropTypes.bool,
      error: PropTypes.bool,
      alerts: PropTypes.bool,
      commands: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  removeSlackDetails: PropTypes.func.isRequired,
};

export default SlackTable;
