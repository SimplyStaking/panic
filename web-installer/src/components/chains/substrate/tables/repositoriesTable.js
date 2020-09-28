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

const RepositoriesTable = (props) => {
  const classes = useStyles();

  const {
    currentChain,
    chainConfig,
    reposConfig,
    removeRepositoryDetails,
  } = props;

  if (chainConfig.byId[currentChain].repositories.length === 0) {
    return <div />;
  }
  return (
    <TableContainer component={Paper}>
      <Table className={classes.table} aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell align="center">Name</TableCell>
            <TableCell align="center">Monitor</TableCell>
            <TableCell align="center">Delete</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {chainConfig.byId[currentChain].repositories.map((id) => (
            <TableRow key={id}>
              <TableCell align="center" component="th" scope="row">
                {reposConfig.byId[id].repoName}
              </TableCell>
              <TableCell align="center">
                {reposConfig.byId[id].monitorRepo ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                <Button onClick={() => { removeRepositoryDetails(reposConfig.byId[id]); }}>
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
  chainConfig: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      repositories: PropTypes.arrayOf(PropTypes.string),
    }).isRequired,
  }).isRequired,
  reposConfig: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      parentId: PropTypes.string,
      repoName: PropTypes.string,
      monitorRepo: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  removeRepositoryDetails: PropTypes.func.isRequired,
  currentChain: PropTypes.string.isRequired,
};

export default RepositoriesTable;
