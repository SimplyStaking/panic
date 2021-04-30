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
  Box,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import CheckIcon from '@material-ui/icons/Check';
import ClearIcon from '@material-ui/icons/Clear';
import CancelIcon from '@material-ui/icons/Cancel';

const SlackTable = ({ slacks, removeSlackDetails }) => {
  if (slacks.allIds.length === 0) {
    return <div />;
  }
  return (
    <Box py={2}>
      <TableContainer component={Paper}>
        <Table className="greyBackground" aria-label="simple table">
          <TableHead>
            <TableRow>
              <TableCell align="center">Slack Name</TableCell>
              <TableCell align="center">Token</TableCell>
              <TableCell align="center">Chat Name</TableCell>
              <TableCell align="center">Info</TableCell>
              <TableCell align="center">Warning</TableCell>
              <TableCell align="center">Critical</TableCell>
              <TableCell align="center">Error</TableCell>
              <TableCell align="center">Alerts</TableCell>
              <TableCell align="center">Commands</TableCell>
              <TableCell align="center">Delete</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {Object.keys(slacks.byId).map((slack) => (
              <TableRow key={slacks.byId[slack].id}>
                <TableCell align="center">
                  {slacks.byId[slack].channel_name}
                </TableCell>
                <TableCell align="center">
                  {slacks.byId[slack].token}
                </TableCell>
                <TableCell align="center">
                  {slacks.byId[slack].chat_name}
                </TableCell>
                <TableCell align="center">
                  {slacks.byId[slack].info ? (
                    <CheckIcon />
                  ) : (
                    <ClearIcon />
                  )}
                </TableCell>
                <TableCell align="center">
                  {slacks.byId[slack].warning ? (
                    <CheckIcon />
                  ) : (
                    <ClearIcon />
                  )}
                </TableCell>
                <TableCell align="center">
                  {slacks.byId[slack].critical ? (
                    <CheckIcon />
                  ) : (
                    <ClearIcon />
                  )}
                </TableCell>
                <TableCell align="center">
                  {slacks.byId[slack].error ? (
                    <CheckIcon />
                  ) : (
                    <ClearIcon />
                  )}
                </TableCell>
                <TableCell align="center">
                  {slacks.byId[slack].alerts ? (
                    <CheckIcon />
                  ) : (
                    <ClearIcon />
                  )}
                </TableCell>
                <TableCell align="center">
                  {slacks.byId[slack].commands ? (
                    <CheckIcon />
                  ) : (
                    <ClearIcon />
                  )}
                </TableCell>
                <TableCell align="center">
                  <Button
                    onClick={() => {
                      removeSlackDetails(slacks.byId[slack]);
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
    </Box>
  );
};

SlackTable.propTypes = {
  slacks: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      channel_name: PropTypes.string,
      token: PropTypes.string,
      chat_name: PropTypes.string,
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
