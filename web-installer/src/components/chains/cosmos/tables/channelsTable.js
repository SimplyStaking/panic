import React from 'react';
import PropTypes from 'prop-types';
import { makeStyles } from '@material-ui/core/styles';
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Button, Grid,
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

const RepositoriesTable = (props) => {
  const classes = useStyles();

  const {
    config,
    removeRepositoryDetails,
  } = props;

  if (config.repositories.length === 0) {
    return <div />;
  }
  return (
    <Grid container className={classes.root} spacing={2}>
      <Grid item xs={12}>
        <Grid container justify="center" spacing={spacing}>
          {[0, 1, 2].map((value) => (
            <Grid key={value} item>
              <Paper className={classes.paper} />
            </Grid>
          ))}
        </Grid>
      </Grid>
    </Grid>
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
          {config.repositories.map((repository) => (
            <TableRow key={repository.repoName}>
              <TableCell component="th" scope="row">
                {repository.repoName}
              </TableCell>
              <TableCell align="center">
                {repository.monitorNode ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                <Button onClick={() => { removeRepositoryDetails(repository); }}>
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

RepositoriesTable.propTypes = {
  config: PropTypes.shape({
    repositories: PropTypes.arrayOf(PropTypes.shape({
      repoName: PropTypes.string.isRequired,
      monitorRepo: PropTypes.bool.isRequired,
    })).isRequired,
  }).isRequired,
  removeRepositoryDetails: PropTypes.func.isRequired,
};

export default RepositoriesTable;
