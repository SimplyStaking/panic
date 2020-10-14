import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Button,
  List, ListItem,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import CheckIcon from '@material-ui/icons/Check';
import ClearIcon from '@material-ui/icons/Clear';
import CancelIcon from '@material-ui/icons/Cancel';

const EmailTable = ({emails, removeEmailDetails}) => {
  if (emails.allIds.length === 0) {
    return <div />;
  }
  return (
    <TableContainer component={Paper}>
      <Table className="greyBackground" aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell align="center">Email Name</TableCell>
            <TableCell align="center">SMTP</TableCell>
            <TableCell align="center">Email From</TableCell>
            <TableCell align="center">Email To</TableCell>
            <TableCell align="center">Username</TableCell>
            <TableCell align="center">Password</TableCell>
            <TableCell align="center">Info</TableCell>
            <TableCell align="center">Warning</TableCell>
            <TableCell align="center">Critical</TableCell>
            <TableCell align="center">Error</TableCell>
            <TableCell align="center">Delete</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {Object.keys(emails.byId).map((email) => (
            <TableRow key={emails.byId[email].id}>
              <TableCell align="center">
                {emails.byId[email].configName}
              </TableCell>
              <TableCell align="center">{emails.byId[email].smtp}</TableCell>
              <TableCell align="center">{emails.byId[email].emailFrom}</TableCell>
              <TableCell align="center">
                <div style={{ maxHeight: 70, overflow: 'auto' }}>
                  <List>
                    {emails.byId[email].emailsTo.map((to) => (
                      <ListItem key={to}>
                        { to }
                      </ListItem>
                    ))}
                  </List>
                </div>
              </TableCell>
              <TableCell align="center">{emails.byId[email].username}</TableCell>
              <TableCell align="center">{emails.byId[email].password}</TableCell>
              <TableCell align="center">
                {emails.byId[email].info ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                {emails.byId[email].warning ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                {emails.byId[email].critical ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                {emails.byId[email].error ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                <Button onClick={() => { removeEmailDetails(emails.byId[email]); }}>
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

EmailTable.propTypes = forbidExtraProps({
  emails: PropTypes.shape({
    byId: PropTypes.shape({
      configName: PropTypes.string,
      smtp: PropTypes.string,
      emailFrom: PropTypes.string,
      emailsTo: PropTypes.arrayOf(PropTypes.string),
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
});

export default EmailTable;
