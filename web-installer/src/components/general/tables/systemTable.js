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

const SystemTable = (props) => {
  const classes = useStyles();

  const {
    systems,
    removeSystemDetails,
  } = props;

  if (systems.length === 0) {
    return <div />;
  }
  return (
    <TableContainer component={Paper}>
      <Table className={classes.table} aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell>Name</TableCell>
            <TableCell>Node Exporter Url</TableCell>
            <TableCell align="center">Monitor</TableCell>
            <TableCell align="center">Delete</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {systems.map((system) => (
            <TableRow key={system.name}>
              <TableCell component="th" scope="row">
                {system.name}
              </TableCell>
              <TableCell component="th" scope="row">
                {system.exporterURL}
              </TableCell>
              <TableCell align="center">
                {system.enabled ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                <Button onClick={() => { removeSystemDetails(system); }}>
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

SystemTable.propTypes = {
  systems: PropTypes.arrayOf(PropTypes.shape({
    name: PropTypes.string.isRequired,
    exporterURL: PropTypes.string.isRequired,
    enabled: PropTypes.bool.isRequired,
  })).isRequired,
  removeSystemDetails: PropTypes.func.isRequired,
};

export default SystemTable;
