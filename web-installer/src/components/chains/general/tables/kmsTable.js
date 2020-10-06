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

const KmsTable = (props) => {
  const classes = useStyles();

  const {
    currentChain,
    chainConfig,
    kmsConfig,
    removeKmsDetails,
  } = props;

  if (chainConfig.byId[currentChain].kmses.length === 0) {
    return <div />;
  }
  return (
    <TableContainer component={Paper}>
      <Table className={classes.table} aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell align="center">Name</TableCell>
            <TableCell align="center">Node Exporter Url</TableCell>
            <TableCell align="center">Monitor</TableCell>
            <TableCell align="center">Delete</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {chainConfig.byId[currentChain].kmses.map((id) => (
            <TableRow key={id}>
              <TableCell align="center">
                {kmsConfig.byId[id].kmsName}
              </TableCell>
              <TableCell align="center">
                {kmsConfig.byId[id].exporterUrl}
              </TableCell>
              <TableCell align="center">
                {kmsConfig.byId[id].monitorKms ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                <Button onClick={() => {
                  removeKmsDetails(kmsConfig.byId[id]);
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

KmsTable.propTypes = {
  chainConfig: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      kmses: PropTypes.arrayOf(PropTypes.string),
    }).isRequired,
  }).isRequired,
  kmsConfig: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      parentId: PropTypes.string,
      kmsName: PropTypes.string,
      exporterUrl: PropTypes.string,
      monitorKms: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  removeKmsDetails: PropTypes.func.isRequired,
  currentChain: PropTypes.string.isRequired,
};

export default KmsTable;
