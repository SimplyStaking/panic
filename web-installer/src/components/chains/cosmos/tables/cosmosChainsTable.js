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

  // Function to clear all references, including the referenced objects
  // from configured object.
  function clearAllChainDetails(chainID) {
    const { removeChainDetails } = props;
    // First remove all the configured nodes
    // Second remove all the configured githubs
    // Third remove all the configured kmses
    // Fourth remove all the configured alerts
    // Finally remove the object itself.
    const payload = {
      id: chainID,
    };
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
};

export default CosmosChainsTable;
