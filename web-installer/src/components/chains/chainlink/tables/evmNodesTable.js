import React from 'react';
import PropTypes from 'prop-types';
import {
  Table,
  TableBody,
  TableContainer,
  TableHead,
  TableRow,
  Button,
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
const EvmNodesTable = ({
  chainConfig, evmNodesConfig, currentChain, removeNodeDetails,
}) => {
  if (chainConfig.byId[currentChain].evmNodes.length === 0) {
    return <div />;
  }

  return (
    <Box pt={5}>
      <TableContainer component={Paper}>
        <Table className="table" aria-label="evm nodes table">
          <TableHead>
            <TableRow>
              <StyledTableCell align="center">Name</StyledTableCell>
              <StyledTableCell align="center">Node HTTP URL</StyledTableCell>
              <StyledTableCell align="center">Monitor Node</StyledTableCell>
              <StyledTableCell align="center">Delete</StyledTableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {chainConfig.byId[currentChain].evmNodes.map((id) => (
              <StyledTableRow key={id}>
                <StyledTableCell align="center">
                  {evmNodesConfig.byId[id].name}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {evmNodesConfig.byId[id].node_http_url}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {evmNodesConfig.byId[id].monitor_node ? <CheckIcon /> : <ClearIcon />}
                </StyledTableCell>
                <StyledTableCell align="center">
                  <Button
                    onClick={() => {
                      removeNodeDetails(evmNodesConfig.byId[id]);
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

EvmNodesTable.propTypes = {
  chainConfig: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      nodes: PropTypes.arrayOf(PropTypes.string),
    }).isRequired,
  }).isRequired,
  evmNodesConfig: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      parent_id: PropTypes.string,
      name: PropTypes.string,
      node_http_url: PropTypes.string,
      monitor_node: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  removeNodeDetails: PropTypes.func.isRequired,
  currentChain: PropTypes.string.isRequired,
};

export default EvmNodesTable;
