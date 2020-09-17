import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import { makeStyles } from '@material-ui/core/styles';
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Button,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import CancelIcon from '@material-ui/icons/Cancel';

const useStyles = makeStyles({
  table: {
    minWidth: 650,
  },
});

const UsersTable = (props) => {
  const classes = useStyles();

  const {
    users,
    removeUserDetails,
  } = props;

  // Do not show users table if there are no users
  if (users.length === 0) {
    return <div />;
  }
  return (
    <TableContainer component={Paper}>
      <Table className={classes.table} aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell align="center">Username</TableCell>
            <TableCell align="center">Password</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {users.map((user) => (
            <TableRow key={user.username}>
              <TableCell component="th" scope="row">
                {user.username}
              </TableCell>
              <TableCell align="center">*************</TableCell>
              <TableCell align="center">
                <Button onClick={() => { removeUserDetails(user); }}>
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

UsersTable.propTypes = forbidExtraProps({
  users: PropTypes.arrayOf(PropTypes.shape({
    username: PropTypes.string.isRequired,
    password: PropTypes.string.isRequired,
  })).isRequired,
  removeUserDetails: PropTypes.func.isRequired,
});

export default UsersTable;
