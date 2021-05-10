import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  List,
  ListItem,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import CancelIcon from '@material-ui/icons/Cancel';
import CheckIcon from '@material-ui/icons/Check';
import ClearIcon from '@material-ui/icons/Clear';

/*
 * Contains the data of all the nodes of the current chain process. Has the
 * functionality to delete node data from redux.
 */
const NodesTable = ({
  chainConfig,
  chainlinkNodesConfig,
  currentChain,
  removeNodeDetails,
}) => {
  if (chainConfig.byId[currentChain].nodes.length === 0) {
    return <div />;
  }

  return (
    <TableContainer component={Paper}>
      <Table className="table" aria-label="chainlink nodes table" style={{ marginBottom: '150px' }}>
        <TableHead>
          <TableRow>
            <TableCell align="center">Name</TableCell>
            <TableCell align="center">Prometheus URLs</TableCell>
            <TableCell align="center">Monitor Prometheus URLs</TableCell>
            <TableCell align="center">Monitor Node</TableCell>
            <TableCell align="center">Delete</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {chainConfig.byId[currentChain].nodes.map((id) => (
            <TableRow key={id}>
              <TableCell align="center">
                {chainlinkNodesConfig.byId[id].name}
              </TableCell>
              <TableCell align="center">
                <div style={{ maxHeight: 70, overflow: 'auto' }}>
                  <List>
                    {chainlinkNodesConfig.byId[id].prometheus_url.map((url) => (
                      <ListItem key={url}>{url}</ListItem>
                    ))}
                  </List>
                </div>
              </TableCell>
              <TableCell align="center">
                {chainlinkNodesConfig.byId[id].monitor_prometheus ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                {chainlinkNodesConfig.byId[id].monitor_node ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                <Button
                  onClick={() => {
                    removeNodeDetails(chainlinkNodesConfig.byId[id]);
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
  chainlinkNodesConfig: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      parent_id: PropTypes.string,
      name: PropTypes.string,
      prometheus_url: PropTypes.string,
      monitor_prometheus: PropTypes.bool,
      monitor_node: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  removeNodeDetails: PropTypes.func.isRequired,
  currentChain: PropTypes.string.isRequired,
});

export default NodesTable;
