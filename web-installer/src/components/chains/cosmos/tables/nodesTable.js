import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
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
    config,
    removeNodeDetails,
  } = props;

  if (config.nodes.length === 0) {
    return <div />;
  }
  return (
    <TableContainer component={Paper}>
      <Table className={classes.table} aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell>Name</TableCell>
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
          {config.nodes.map((node) => (
            <TableRow key={node.cosmosNodeName}>
              <TableCell component="th" scope="row">
                {node.cosmosNodeName}
              </TableCell>
              <TableCell align="center">{node.tendermintRPCURL}</TableCell>
              <TableCell align="center">{node.cosmosRPCURL}</TableCell>
              <TableCell align="center">{node.prometheusURL}</TableCell>
              <TableCell align="center">{node.exporterURL}</TableCell>
              <TableCell align="center">
                {node.isValidator ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                {node.monitorNode ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                {node.isArchiveNode ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                {node.useAsDataSource ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                <Button onClick={() => { removeNodeDetails(node); }}>
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
  config: PropTypes.shape({
    nodes: PropTypes.arrayOf(PropTypes.shape({
      cosmosNodeName: PropTypes.string.isRequired,
      tendermintRPCURL: PropTypes.string.isRequired,
      cosmosRPCURL: PropTypes.string.isRequired,
      prometheusURL: PropTypes.string.isRequired,
      exporterURL: PropTypes.string.isRequired,
      isValidator: PropTypes.bool.isRequired,
      monitorNode: PropTypes.bool.isRequired,
      isArchiveNode: PropTypes.bool.isRequired,
      useAsDataSource: PropTypes.bool.isRequired,
    })).isRequired,
  }).isRequired,
  removeNodeDetails: PropTypes.func.isRequired,
});

export default NodesTable;
