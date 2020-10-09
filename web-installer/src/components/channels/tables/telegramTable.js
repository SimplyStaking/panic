import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Button,
  Box,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import CheckIcon from '@material-ui/icons/Check';
import ClearIcon from '@material-ui/icons/Clear';
import CancelIcon from '@material-ui/icons/Cancel';

const TelegramTable = ({telegrams, removeTelegramDetails}) => {
  if (telegrams.allIds.length === 0) {
    return <div />;
  }
  return (
    <Box py={2}>
      <TableContainer component={Paper}>
        <Table className="greyBackground" aria-label="simple table">
          <TableHead>
            <TableRow>
              <TableCell align="center">Telegram Name</TableCell>
              <TableCell align="center">Token</TableCell>
              <TableCell align="center">Chat ID</TableCell>
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
            {Object.keys(telegrams.byId).map((telegram) => (
              <TableRow key={telegrams.byId[telegram].id}>
                <TableCell align="center">
                  {telegrams.byId[telegram].botName}
                </TableCell>
                <TableCell align="center">
                  {telegrams.byId[telegram].botToken}
                </TableCell>
                <TableCell align="center">
                  {telegrams.byId[telegram].chatID}
                </TableCell>
                <TableCell align="center">
                  {telegrams.byId[telegram].info
                    ? <CheckIcon /> : <ClearIcon />}
                </TableCell>
                <TableCell align="center">
                  {telegrams.byId[telegram].warning
                    ? <CheckIcon /> : <ClearIcon />}
                </TableCell>
                <TableCell align="center">
                  {telegrams.byId[telegram].critical
                    ? <CheckIcon /> : <ClearIcon />}
                </TableCell>
                <TableCell align="center">
                  {telegrams.byId[telegram].error
                    ? <CheckIcon /> : <ClearIcon />}
                </TableCell>
                <TableCell align="center">
                  {telegrams.byId[telegram].alerts
                    ? <CheckIcon /> : <ClearIcon />}
                </TableCell>
                <TableCell align="center">
                  {telegrams.byId[telegram].commands
                    ? <CheckIcon /> : <ClearIcon />}
                </TableCell>
                <TableCell align="center">
                  <Button onClick={() => {
                      removeTelegramDetails(telegrams.byId[telegram]); 
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

TelegramTable.propTypes = forbidExtraProps({
  telegrams: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      botName: PropTypes.string,
      botToken: PropTypes.string,
      chatID: PropTypes.string,
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
});

export default TelegramTable;
