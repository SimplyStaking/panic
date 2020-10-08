import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import { DeleteAccount } from '../../utils/buttons';

const UsersTable = ({users, removeUserDetails}) => {
  // Do not show users table if there are no users
  if (users.length === 0) {
    return <div />;
  }
  return (
    <TableContainer component={Paper}>
      <Table className="table" aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell align="center">Username</TableCell>
            <TableCell align="center">Password</TableCell>
            <TableCell align="center">Delete</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {users.map((user) => (
            <TableRow key={user.username}>
              <TableCell align="center">
                {user.username}
              </TableCell>
              <TableCell align="center">*************</TableCell>
              <TableCell align="center">
                <DeleteAccount
                  username={user.username}
                  removeFromRedux={removeUserDetails}
                />
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
