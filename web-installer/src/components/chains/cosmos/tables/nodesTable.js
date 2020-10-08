import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Button,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import CheckIcon from '@material-ui/icons/Check';
import ClearIcon from '@material-ui/icons/Clear';
import CancelIcon from '@material-ui/icons/Cancel';

/*
 * Contains the data of all the nodes of the current chain process. Has the
 * functionality to delete node data from redux.
 */
const NodesTable = ({chainConfig, nodesConfig, currentChain, removeNodeDetails
  }) => {
  if (chainConfig.byId[currentChain].nodes.length === 0) {
    return <div />;
  }

  return (
    <TableContainer component={Paper}>
      <Table className="table" aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell align="center">Name</TableCell>
            <TableCell align="center">Tendermint</TableCell>
            <TableCell align="center">Cosmos SDK</TableCell>
            <TableCell align="center">Prometheus</TableCell>
            <TableCell align="center">Node Exporter</TableCell>
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
              <TableCell align="center">
                {nodesConfig.byId[id].cosmosNodeName}
              </TableCell>
              <TableCell align="center">
                {nodesConfig.byId[id].tendermintRpcUrl}
              </TableCell>
              <TableCell align="center">
                {nodesConfig.byId[id].cosmosRpcUrl}
              </TableCell>
              <TableCell align="center">
                {nodesConfig.byId[id].prometheusUrl}
              </TableCell>
              <TableCell align="center">
                {nodesConfig.byId[id].exporterUrl}
              </TableCell>
              <TableCell align="center">
                {nodesConfig.byId[id].isValidator
                  ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                {nodesConfig.byId[id].monitorNode
                  ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                {nodesConfig.byId[id].isArchiveNode
                  ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                {nodesConfig.byId[id].useAsDataSource
                  ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                <Button onClick={() => {
                  removeNodeDetails(nodesConfig.byId[id]);
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

NodesTable.propTypes = forbidExtraProps({
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
      cosmosNodeName: PropTypes.string,
      tendermintRpcUrl: PropTypes.string,
      cosmosRpcUrl: PropTypes.string,
      prometheusUrl: PropTypes.string,
      exporterUrl: PropTypes.string,
      isValidator: PropTypes.bool,
      monitorNode: PropTypes.bool,
      isArchiveNode: PropTypes.bool,
      useAsDataSource: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  removeNodeDetails: PropTypes.func.isRequired,
  currentChain: PropTypes.string.isRequired,
});

export default NodesTable;
