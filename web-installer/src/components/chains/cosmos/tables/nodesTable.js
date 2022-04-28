import React from 'react';
import PropTypes from 'prop-types';
import {
  Table, TableBody, TableContainer, TableHead, TableRow, Button, Box,
  Grid,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import CheckIcon from '@material-ui/icons/Check';
import ClearIcon from '@material-ui/icons/Clear';
import CancelIcon from '@material-ui/icons/Cancel';
import StyledTableRow from 'assets/jss/custom-jss/StyledTableRow';
import StyledTableCell from 'assets/jss/custom-jss/StyledTableCell';
import { NEXT, BACK } from 'constants/constants';
import StepButtonContainer from 'containers/chains/common/stepButtonContainer';

/*
 * Contains the data of all the nodes of the current chain process. Has the
 * functionality to delete node data from redux.
 */
const NodesTable = ({
  chainConfig, cosmosNodesConfig, currentChain, removeNodeDetails, data,
}) => {
  if (chainConfig.byId[currentChain].nodes.length === 0) {
    return (
      <div>
        <Box py={4}>
          <Grid container spacing={3} justifyContent="center" alignItems="center">
            <Grid item xs={4} />
            <Grid item xs={2}>
              <StepButtonContainer
                disabled={false}
                text={BACK}
                navigation={data.nodeForm.backStep}
              />
            </Grid>
            <Grid item xs={2}>
              <StepButtonContainer
                disabled={false}
                text={NEXT}
                navigation={data.nodeForm.nextStep}
              />
            </Grid>
            <Grid item xs={4} />
          </Grid>
        </Box>
      </div>
    );
  }

  return (
    <Box pt={5}>
      <TableContainer component={Paper}>
        <Table className="table" aria-label="cosmos-nodes-table">
          <TableHead>
            <TableRow>
              <StyledTableCell align="center">Name</StyledTableCell>
              <StyledTableCell align="center">Cosmos Rest URL</StyledTableCell>
              <StyledTableCell align="center">Prometheus</StyledTableCell>
              <StyledTableCell align="center">Node Exporter</StyledTableCell>
              <StyledTableCell align="center">Operator Address</StyledTableCell>
              <StyledTableCell align="center">Validator</StyledTableCell>
              <StyledTableCell align="center">Monitor Prometheus</StyledTableCell>
              <StyledTableCell align="center">Monitor Cosmos Rest</StyledTableCell>
              <StyledTableCell align="center">Monitor System</StyledTableCell>
              <StyledTableCell align="center">Monitor Node</StyledTableCell>
              <StyledTableCell align="center">Archive</StyledTableCell>
              <StyledTableCell align="center">Data Source</StyledTableCell>
              <StyledTableCell align="center">Delete</StyledTableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {chainConfig.byId[currentChain].nodes.map((id) => (
              <StyledTableRow key={id}>
                <StyledTableCell align="center">{cosmosNodesConfig.byId[id].name}</StyledTableCell>
                <StyledTableCell align="center">
                  {cosmosNodesConfig.byId[id].cosmos_rest_url}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {cosmosNodesConfig.byId[id].prometheus_url}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {cosmosNodesConfig.byId[id].exporter_url}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {cosmosNodesConfig.byId[id].operator_address}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {cosmosNodesConfig.byId[id].is_validator ? <CheckIcon /> : <ClearIcon />}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {cosmosNodesConfig.byId[id].monitor_prometheus ? <CheckIcon /> : <ClearIcon />}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {cosmosNodesConfig.byId[id].monitor_cosmos_rest ? <CheckIcon /> : <ClearIcon />}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {cosmosNodesConfig.byId[id].monitor_system ? <CheckIcon /> : <ClearIcon />}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {cosmosNodesConfig.byId[id].monitor_node ? <CheckIcon /> : <ClearIcon />}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {cosmosNodesConfig.byId[id].is_archive_node ? <CheckIcon /> : <ClearIcon />}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {cosmosNodesConfig.byId[id].use_as_data_source ? <CheckIcon /> : <ClearIcon />}
                </StyledTableCell>
                <StyledTableCell align="center">
                  <Button
                    onClick={() => {
                      removeNodeDetails(cosmosNodesConfig.byId[id]);
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
      <Box py={4}>
        <Grid container spacing={3} justifyContent="center" alignItems="center">
          <Grid item xs={4} />
          <Grid item xs={2}>
            <StepButtonContainer
              disabled={false}
              text={BACK}
              navigation={data.nodeForm.backStep}
            />
          </Grid>
          <Grid item xs={2}>
            <StepButtonContainer
              disabled={false}
              text={NEXT}
              navigation={data.nodeForm.nextStep}
            />
          </Grid>
          <Grid item xs={4} />
        </Grid>
      </Box>
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
  cosmosNodesConfig: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      parent_id: PropTypes.string,
      name: PropTypes.string,
      cosmos_rpc_url: PropTypes.string,
      prometheus_url: PropTypes.string,
      exporter_url: PropTypes.string,
      is_validator: PropTypes.bool,
      monitor_node: PropTypes.bool,
      is_archive_node: PropTypes.bool,
      use_as_data_source: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  removeNodeDetails: PropTypes.func.isRequired,
  currentChain: PropTypes.string.isRequired,
  data: PropTypes.shape({
    nodeForm: PropTypes.shape({
      backStep: PropTypes.string.isRequired,
      nextStep: PropTypes.string.isRequired,
    }).isRequired,
  }).isRequired,
};

export default NodesTable;
