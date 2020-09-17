import React from 'react';
import PropTypes from 'prop-types';
import { makeStyles } from '@material-ui/core/styles';
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Button,
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

const GithubsTable = (props) => {
  const classes = useStyles();

  const {
    repositories,
    removeGithubDetails,
  } = props;

  if (repositories.length === 0) {
    return <div />;
  }
  return (
    <TableContainer component={Paper}>
      <Table className={classes.table} aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell>Name</TableCell>
            <TableCell align="center">Monitor</TableCell>
            <TableCell align="center">Delete</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {repositories.map((repository) => (
            <TableRow key={repository.repoName}>
              <TableCell component="th" scope="row">
                {repository.repoName}
              </TableCell>
              <TableCell align="center">
                {repository.enabled ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                <Button onClick={() => { removeGithubDetails(repository); }}>
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

GithubsTable.propTypes = {
  repositories: PropTypes.arrayOf(PropTypes.shape({
    name: PropTypes.string.isRequired,
    enabled: PropTypes.bool.isRequired,
  })).isRequired,
  removeGithubDetails: PropTypes.func.isRequired,
};

export default GithubsTable;
