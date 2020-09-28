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
import { GLOBAL } from '../../../constants/constants';

const useStyles = makeStyles({
  table: {
    minWidth: 650,
  },
});

const RepositoryTable = (props) => {
  const classes = useStyles();

  const {
    config,
    repositories,
    removeRepositoryDetails,
  } = props;

  if (config.repositories.length === 0) {
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
          {config.repositories.map((id) => (
            <TableRow key={id}>
              <TableCell align="center">
                {repositories.byId[id].repoName}
              </TableCell>
              <TableCell align="center">
                {repositories.byId[id].monitorRepo ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                <Button onClick={() => {
                  removeRepositoryDetails({
                    id,
                    parentId: GLOBAL,
                  });
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
  );
};

RepositoryTable.propTypes = {
  config: PropTypes.shape({
    repositories: PropTypes.arrayOf(PropTypes.string),
  }).isRequired,
  repositories: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      repoName: PropTypes.string,
      monitorRepo: PropTypes.bool,
    }).isRequired,
  }).isRequired,
  removeRepositoryDetails: PropTypes.func.isRequired,
};

export default RepositoryTable;
