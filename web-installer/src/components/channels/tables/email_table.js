import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import { makeStyles } from '@material-ui/core/styles';
import {
  Table,
  TableBody,
  TableCell,
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

const useStyles = makeStyles({
  table: {
    minWidth: 650,
  },
});

const EmailTable = (props) => {
  const classes = useStyles();

  const {
    emails,
    removeEmailDetails,
  } = props;

  if (emails.length === 0) {
    return <div />;
  }
  return (
    <TableContainer component={Paper}>
      <Table className={classes.table} aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell>Name</TableCell>
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
          {emails.map((email) => (
            <TableRow key={email.configName}>
              <TableCell component="th" scope="row">
                {email.configName}
              </TableCell>
              <TableCell align="center">{email.smtp}</TableCell>
              <TableCell align="center">{email.emailFrom}</TableCell>
              <TableCell align="center">
                <div style={{ maxHeight: 70, overflow: 'auto' }}>
                  <List>
                    {email.emailsTo.map((to) => (
                      <ListItem key={to}>
                        { to }
                      </ListItem>
                    ))}
                  </List>
                </div>
              </TableCell>
              <TableCell align="center">{email.username}</TableCell>
              <TableCell align="center">{email.password}</TableCell>
              <TableCell align="center">
                {email.info ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                {email.warning ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                {email.critical ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                {email.error ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                <Button onClick={() => { removeEmailDetails(email); }}>
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
  emails: PropTypes.arrayOf(PropTypes.shape({
    configName: PropTypes.string.isRequired,
    smtp: PropTypes.string.isRequired,
    emailFrom: PropTypes.string.isRequired,
    emailsTo: PropTypes.arrayOf(PropTypes.string.isRequired).isRequired,
    username: PropTypes.string.isRequired,
    password: PropTypes.string.isRequired,
    info: PropTypes.bool.isRequired,
    warning: PropTypes.bool.isRequired,
    critical: PropTypes.bool.isRequired,
    error: PropTypes.bool.isRequired,
  })).isRequired,
  removeEmailDetails: PropTypes.func.isRequired,
});

export default EmailTable;
