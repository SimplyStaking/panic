import React from 'react';
import PropTypes from 'prop-types';
import { makeStyles } from '@material-ui/core/styles';
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Button,
} from '@material-ui/core';
import CancelIcon from '@material-ui/icons/Cancel';
import Paper from '@material-ui/core/Paper';
// import { COSMOS_SETUP_PAGE } from '../../../../constants/constants';

const useStyles = makeStyles({
  table: {
    minWidth: 650,
  },
});

/* Temporarily removing management of already added configurations */

const CosmosChainsTable = (props) => {
  const classes = useStyles();

  const {
    config,
    // loadConfigDetails,
  } = props;

  // const manageConfiguration = (page, config) => {
  //   const { pageChanger } = props;
  //   pageChanger({ page });
  //   loadConfigDetails(config);
  // };

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
            <TableCell>Name</TableCell>
            {/* <TableCell align="center">Manage</TableCell> */}
            <TableCell align="center">Delete</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {config.allIds.map((id) => (
            <TableRow key={id}>
              <TableCell component="th" scope="row">
                {config.byId[id].chainName}
              </TableCell>
              {/* <TableCell component="th" scope="row">
                <Box px={2}>
                  <Button onClick={() => {
                    manageConfiguration(COSMOS_SETUP_PAGE, config);
                  }}
                  >
                    Manage
                  </Button>
                </Box>
              </TableCell> */}
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
  // loadConfigDetails: PropTypes.func.isRequired,
};

export default CosmosChainsTable;
