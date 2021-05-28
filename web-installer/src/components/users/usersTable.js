import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import {
  Table, TableBody, TableContainer, TableHead, TableRow, Box,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import { DeleteAccount } from 'utils/buttons';
import StyledTableRow from 'assets/jss/custom-jss/StyledTableRow';
import StyledTableCell from 'assets/jss/custom-jss/StyledTableCell';

const UsersTable = ({ users, removeUserDetails }) => {
  // Do not show users table if there are no users
  if (users.length === 0) {
    return <div />;
  }
  return (
    <Box pt={8}>
      <TableContainer component={Paper}>
        <Table className="table" aria-label="users table">
          <TableHead>
            <TableRow>
              <StyledTableCell align="center">Username</StyledTableCell>
              <StyledTableCell align="center">Password</StyledTableCell>
              <StyledTableCell align="center">Delete</StyledTableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {users.map((username) => (
              <StyledTableRow key={username}>
                <StyledTableCell align="center">{username}</StyledTableCell>
                <StyledTableCell align="center">*************</StyledTableCell>
                <StyledTableCell align="center">
                  <DeleteAccount
                    username={username}
                    removeFromRedux={removeUserDetails}
                  />
                </StyledTableCell>
              </StyledTableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

UsersTable.propTypes = forbidExtraProps({
  users: PropTypes.arrayOf(
    PropTypes.shape({
      username: PropTypes.string.isRequired,
      password: PropTypes.string.isRequired,
    }),
  ).isRequired,
  removeUserDetails: PropTypes.func.isRequired,
});

export default UsersTable;
