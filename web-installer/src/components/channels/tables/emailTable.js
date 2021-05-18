import React from 'react';
import PropTypes from 'prop-types';
import {
  Table,
  TableBody,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  List,
  ListItem,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import CheckIcon from '@material-ui/icons/Check';
import ClearIcon from '@material-ui/icons/Clear';
import CancelIcon from '@material-ui/icons/Cancel';
import StyledTableRow from 'assets/jss/custom-jss/StyledTableRow';
import StyledTableCell from 'assets/jss/custom-jss/StyledTableCell';

const EmailTable = ({ emails, removeEmailDetails }) => {
  if (emails.allIds.length === 0) {
    return <div />;
  }
  return (
    <TableContainer component={Paper}>
      <Table className="greyBackground" aria-label="emails table">
        <TableHead>
          <TableRow>
            <StyledTableCell align="center">Email Name</StyledTableCell>
            <StyledTableCell align="center">SMTP</StyledTableCell>
            <StyledTableCell align="center">Port</StyledTableCell>
            <StyledTableCell align="center">Email From</StyledTableCell>
            <StyledTableCell align="center">Email To</StyledTableCell>
            <StyledTableCell align="center">Username</StyledTableCell>
            <StyledTableCell align="center">Password</StyledTableCell>
            <StyledTableCell align="center">Info</StyledTableCell>
            <StyledTableCell align="center">Warning</StyledTableCell>
            <StyledTableCell align="center">Critical</StyledTableCell>
            <StyledTableCell align="center">Error</StyledTableCell>
            <StyledTableCell align="center">Delete</StyledTableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {Object.keys(emails.byId).map((email) => (
            <StyledTableRow key={emails.byId[email].id}>
              <StyledTableCell align="center">
                {emails.byId[email].channel_name}
              </StyledTableCell>
              <StyledTableCell align="center">{emails.byId[email].smtp}</StyledTableCell>
              <StyledTableCell align="center">{emails.byId[email].port}</StyledTableCell>
              <StyledTableCell align="center">
                {emails.byId[email].email_from}
              </StyledTableCell>
              <StyledTableCell align="center">
                <div style={{ maxHeight: 70, overflow: 'auto' }}>
                  <List>
                    {emails.byId[email].emails_to.map((to) => (
                      <ListItem key={to}>{to}</ListItem>
                    ))}
                  </List>
                </div>
              </StyledTableCell>
              <StyledTableCell align="center">
                {emails.byId[email].username}
              </StyledTableCell>
              <StyledTableCell align="center">
                {emails.byId[email].password}
              </StyledTableCell>
              <StyledTableCell align="center">
                {emails.byId[email].info ? <CheckIcon /> : <ClearIcon />}
              </StyledTableCell>
              <StyledTableCell align="center">
                {emails.byId[email].warning ? <CheckIcon /> : <ClearIcon />}
              </StyledTableCell>
              <StyledTableCell align="center">
                {emails.byId[email].critical ? <CheckIcon /> : <ClearIcon />}
              </StyledTableCell>
              <StyledTableCell align="center">
                {emails.byId[email].error ? <CheckIcon /> : <ClearIcon />}
              </StyledTableCell>
              <StyledTableCell align="center">
                <Button
                  onClick={() => {
                    removeEmailDetails(emails.byId[email]);
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
  );
};

EmailTable.propTypes = {
  emails: PropTypes.shape({
    byId: PropTypes.shape({
      channel_name: PropTypes.string,
      smtp: PropTypes.string,
      port: PropTypes.number,
      email_from: PropTypes.string,
      emails_to: PropTypes.arrayOf(PropTypes.string),
      username: PropTypes.string,
      password: PropTypes.string,
      info: PropTypes.bool,
      warning: PropTypes.bool,
      critical: PropTypes.bool,
      error: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  removeEmailDetails: PropTypes.func.isRequired,
};

export default EmailTable;
