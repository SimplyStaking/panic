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

const KMSTable = (props) => {
  const classes = useStyles();

  const {
    config,
    removeKMSDetails,
  } = props;

  if (config.kmses.length === 0) {
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
          {config.kmses.map((kms) => (
            <TableRow key={kms.kmsName}>
              <TableCell component="th" scope="row">
                {kms.kmsName}
              </TableCell>
              <TableCell component="th" scope="row">
                {kms.exporterURL}
              </TableCell>
              <TableCell align="center">
                {kms.monitorKMS ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                <Button onClick={() => { removeKMSDetails(kms); }}>
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

KMSTable.propTypes = {
  config: PropTypes.shape({
    kmses: PropTypes.arrayOf(PropTypes.shape({
      kmsName: PropTypes.string.isRequired,
      exporterURL: PropTypes.string.isRequired,
      monitorKMS: PropTypes.bool.isRequired,
    })).isRequired,
  }).isRequired,
  removeKMSDetails: PropTypes.func.isRequired,
};

export default KMSTable;
