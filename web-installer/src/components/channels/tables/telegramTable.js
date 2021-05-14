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
import { withStyles } from '@material-ui/core/styles';
import Paper from '@material-ui/core/Paper';
import CheckIcon from '@material-ui/icons/Check';
import ClearIcon from '@material-ui/icons/Clear';
import CancelIcon from '@material-ui/icons/Cancel';

const StyledTableCell = withStyles((theme) => ({
  head: {
    backgroundColor: '#363946',
    color: theme.palette.common.white,
  },
  body: {
    fontSize: 14,
  },
}))(TableCell);

const StyledTableRow = withStyles((theme) => ({
  root: {
    '&:nth-of-type(odd)': {
      backgroundColor: theme.palette.action.hover,
    },
  },
}))(TableRow);

const TelegramTable = ({ telegrams, removeTelegramDetails }) => {
  if (telegrams.allIds.length === 0) {
    return <div />;
  }
  return (
    <Box pt={8}>
      <TableContainer component={Paper}>
        <Table className="greyBackground" aria-label="simple table">
          <TableHead>
            <TableRow>
              <StyledTableCell> Telegram Name </StyledTableCell>
              <StyledTableCell align="right">Token</StyledTableCell>
              <StyledTableCell align="right">Chat ID</StyledTableCell>
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
            {Object.keys(telegrams.byId).map((telegram) => (
              <StyledTableRow key={telegrams.byId[telegram].id}>
                <StyledTableCell>
                  {telegrams.byId[telegram].channel_name}
                </StyledTableCell>
                <StyledTableCell align="right">
                  {telegrams.byId[telegram].bot_token}
                </StyledTableCell>
                <StyledTableCell align="right">
                  {telegrams.byId[telegram].chat_id}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {telegrams.byId[telegram].info ? (
                    <CheckIcon />
                  ) : (
                    <ClearIcon />
                  )}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {telegrams.byId[telegram].warning ? (
                    <CheckIcon />
                  ) : (
                    <ClearIcon />
                  )}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {telegrams.byId[telegram].critical ? (
                    <CheckIcon />
                  ) : (
                    <ClearIcon />
                  )}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {telegrams.byId[telegram].error ? (
                    <CheckIcon />
                  ) : (
                    <ClearIcon />
                  )}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {telegrams.byId[telegram].alerts ? (
                    <CheckIcon />
                  ) : (
                    <ClearIcon />
                  )}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {telegrams.byId[telegram].commands ? (
                    <CheckIcon />
                  ) : (
                    <ClearIcon />
                  )}
                </StyledTableCell>
                <StyledTableCell align="center">
                  <Button
                    onClick={() => {
                      removeTelegramDetails(telegrams.byId[telegram]);
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

TelegramTable.propTypes = {
  telegrams: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      channel_name: PropTypes.string,
      bot_token: PropTypes.string,
      chat_id: PropTypes.string,
      info: PropTypes.bool,
      warning: PropTypes.bool,
      critical: PropTypes.bool,
      error: PropTypes.bool,
      alerts: PropTypes.bool,
      commands: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  removeTelegramDetails: PropTypes.func.isRequired,
};

export default TelegramTable;
