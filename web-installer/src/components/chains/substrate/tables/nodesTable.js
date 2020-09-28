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

const NodesTable = (props) => {
  const classes = useStyles();

  const {
    chainConfig,
    nodesConfig,
    currentChain,
    removeNodeDetails,
  } = props;

  if (chainConfig.byId[currentChain].nodes.length === 0) {
    return <div />;
  }
  return (
    <TableContainer component={Paper}>
      <Table className={classes.table} aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell align="center">Name</TableCell>
            <TableCell align="center">Websocket</TableCell>
            <TableCell align="center">Telemetry</TableCell>
            <TableCell align="center">Prometheus</TableCell>
            <TableCell align="center">Node Exporter</TableCell>
            <TableCell align="center">Stash Address</TableCell>
            <TableCell align="center">Validator</TableCell>
            <TableCell align="center">Monitor</TableCell>
            <TableCell align="center">Archive</TableCell>
            <TableCell align="center">Data Source</TableCell>
            <TableCell align="center">Delete</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {chainConfig.byId[currentChain].nodes.map((id) => (
            <TableRow key={id}>
              <TableCell align="center" component="th" scope="row">
                {nodesConfig.byId[id].substrateNodeName}
              </TableCell>
              <TableCell align="center">{nodesConfig.byId[id].nodeWSURL}</TableCell>
              <TableCell align="center">{nodesConfig.byId[id].telemetryURL}</TableCell>
              <TableCell align="center">{nodesConfig.byId[id].prometheusURL}</TableCell>
              <TableCell align="center">{nodesConfig.byId[id].exporterURL}</TableCell>
              <TableCell align="center">{nodesConfig.byId[id].stashAddress}</TableCell>
              <TableCell align="center">
                {nodesConfig.byId[id].isValidator ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                {nodesConfig.byId[id].monitorNode ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                {nodesConfig.byId[id].isArchiveNode ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                {nodesConfig.byId[id].useAsDataSource ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                <Button onClick={() => { removeNodeDetails(nodesConfig.byId[id]); }}>
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

NodesTable.propTypes = {
  chainConfig: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      nodes: PropTypes.arrayOf(PropTypes.string),
    }).isRequired,
  }).isRequired,
  nodesConfig: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      parentId: PropTypes.string,
      substrateNodeName: PropTypes.string.isRequired,
      nodeWSURL: PropTypes.string,
      telemetryURL: PropTypes.string,
      prometheusURL: PropTypes.string,
      exporterURL: PropTypes.string,
      stashAddress: PropTypes.string,
      isValidator: PropTypes.bool,
      monitorNode: PropTypes.bool,
      isArchiveNode: PropTypes.bool,
      useAsDataSource: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  removeNodeDetails: PropTypes.func.isRequired,
  currentChain: PropTypes.string.isRequired,
};

export default NodesTable;
