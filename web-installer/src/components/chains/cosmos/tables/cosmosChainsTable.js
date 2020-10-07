import React from 'react';
import PropTypes from 'prop-types';
import { makeStyles } from '@material-ui/core/styles';
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Button, Box,
} from '@material-ui/core';
import CancelIcon from '@material-ui/icons/Cancel';
import Paper from '@material-ui/core/Paper';
import { COSMOS_SETUP_PAGE } from '../../../../constants/constants';

const useStyles = makeStyles({
  table: {
    minWidth: 650,
  },
});

/*
 * Displays all the names of the configured chains, in the chain accordion.
 * Has functionality to load a chains configuration as well as clear all data
 * setup for a chain.
*/
const CosmosChainsTable = (props) => {
  const classes = useStyles();

  const {
    config,
    loadConfigDetails,
  } = props;

  const loadConfiguration = (page, id) => {
    const { pageChanger } = props;
    loadConfigDetails({ id });
    pageChanger({ page });
  };

  // We have to clean up all the other reducers once a chain configuration
  // is completely removed
  function clearAllChainDetails(chainID) {
    const {
      removeChainDetails,
      removeNodeDetails,
      removeRepositoryDetails,
      removeKmsDetails,
    } = props;
    // Assign buffer variable for easier readability
    const currentConfig = config.byId[chainID];
    const payload = { parentId: chainID, id: '' };

    // Clear all the configured nodes from state
    for (let i = 0; i < currentConfig.nodes.length; i += 1) {
      payload.id = currentConfig.nodes[i];
      removeNodeDetails(payload);
    }

    // Clear all the configured repositories from state
    for (let i = 0; i < currentConfig.repositories.length; i += 1) {
      payload.id = currentConfig.repositories[i];
      removeRepositoryDetails(payload);
    }

    // Clear all the configured kmses from state
    for (let i = 0; i < currentConfig.kmses.length; i += 1) {
      payload.id = currentConfig.kmses[i];
      removeKmsDetails(payload);
    }

    // Finally clear the chain from the configuration
    payload.id = chainID;
    removeChainDetails(payload);
  }

  if (config.allIds.length === 0) {
    return <div />;
  }
  return (
    <TableContainer component={Paper}>
      <Table className={classes.table} aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell align="center">Name</TableCell>
            <TableCell align="center">Manage</TableCell>
            <TableCell align="center">Delete</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {config.allIds.map((id) => (
            <TableRow key={id}>
              <TableCell align="center">
                {config.byId[id].chainName}
              </TableCell>
              <TableCell align="center">
                <Box px={2}>
                  <Button onClick={() => {
                    loadConfiguration(COSMOS_SETUP_PAGE, id);
                  }}
                  >
                    Load
                  </Button>
                </Box>
              </TableCell>
              <TableCell align="center">
                <Button onClick={() => {
                  clearAllChainDetails(id);
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

CosmosChainsTable.propTypes = {
  config: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      chainName: PropTypes.string,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string.isRequired).isRequired,
  }).isRequired,
  removeChainDetails: PropTypes.func.isRequired,
  loadConfigDetails: PropTypes.func.isRequired,
  pageChanger: PropTypes.func.isRequired,
  removeNodeDetails: PropTypes.func.isRequired,
  removeRepositoryDetails: PropTypes.func.isRequired,
  removeKmsDetails: PropTypes.func.isRequired,
};

export default CosmosChainsTable;
