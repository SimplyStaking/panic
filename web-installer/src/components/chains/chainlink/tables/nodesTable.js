import React from 'react';
import PropTypes from 'prop-types';
import {
  Table,
  TableBody,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  List,
  ListItem,
  Box,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import StyledTableRow from 'assets/jss/custom-jss/StyledTableRow';
import StyledTableCell from 'assets/jss/custom-jss/StyledTableCell';
import CancelIcon from '@material-ui/icons/Cancel';
import CheckIcon from '@material-ui/icons/Check';
import ClearIcon from '@material-ui/icons/Clear';

/*
 * Contains the data of all the nodes of the current chain process. Has the
 * functionality to delete node data from redux.
 */
const NodesTable = ({
  chainConfig, chainlinkNodesConfig, currentChain, removeNodeDetails,
}) => {
  if (chainConfig.byId[currentChain].nodes.length === 0) {
    return <div />;
  }

  return (
    <Box pt={5}>
      <TableContainer component={Paper}>
        <Table className="table" aria-label="chainlink nodes table">
          <TableHead>
            <TableRow>
              <StyledTableCell align="center">Name</StyledTableCell>
              <StyledTableCell align="center">Prometheus URLs</StyledTableCell>
              <StyledTableCell align="center">Ethereum Addresses</StyledTableCell>
              <StyledTableCell align="center">Monitor Prometheus URLs</StyledTableCell>
              <StyledTableCell align="center">Monitor Node</StyledTableCell>
              <StyledTableCell align="center">Delete</StyledTableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {chainConfig.byId[currentChain].nodes.map((id) => (
              <StyledTableRow key={id}>
                <StyledTableCell align="center">
                  {chainlinkNodesConfig.byId[id].name}
                </StyledTableCell>
                <StyledTableCell align="center">
                  <div style={{ maxHeight: 70, overflow: 'auto' }}>
                    <List>
                      {chainlinkNodesConfig.byId[id].prometheus_url.map((url) => (
                        <ListItem key={url}>{url}</ListItem>
                      ))}
                    </List>
                  </div>
                </StyledTableCell>
                <StyledTableCell align="center">
                  <div style={{ maxHeight: 70, overflow: 'auto' }}>
                    <List>
                      {chainlinkNodesConfig.byId[id].node_address.map((address) => (
                        <ListItem key={address}>{address}</ListItem>
                      ))}
                    </List>
                  </div>
                </StyledTableCell>
                <StyledTableCell align="center">
                  {chainlinkNodesConfig.byId[id].monitor_prometheus ? <CheckIcon /> : <ClearIcon />}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {chainlinkNodesConfig.byId[id].monitor_node ? <CheckIcon /> : <ClearIcon />}
                </StyledTableCell>
                <StyledTableCell align="center">
                  <Button
                    onClick={() => {
                      removeNodeDetails(chainlinkNodesConfig.byId[id]);
                    }}
                  >
                    <CancelIcon />
                  </Button>
                </StyledTableCell>
              </StyledTableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

NodesTable.propTypes = {
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
      node_address: PropTypes.string,
      monitor_prometheus: PropTypes.bool,
      monitor_node: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  removeNodeDetails: PropTypes.func.isRequired,
  currentChain: PropTypes.string.isRequired,
};

export default NodesTable;
