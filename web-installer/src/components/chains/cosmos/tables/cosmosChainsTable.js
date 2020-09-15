import React from 'react';
import PropTypes from 'prop-types';
import { makeStyles } from '@material-ui/core/styles';
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Button, Box,
} from '@material-ui/core';
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
    cosmosConfigs,
    loadConfigDetails,
    removeConfigDetails,
  } = props;

  const manageConfiguration = (page, config) => {
    const { pageChanger } = props;
    pageChanger({ page });
    loadConfigDetails(config);
  };

  return (
    <TableContainer component={Paper}>
      <Table className={classes.table} aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell>Name</TableCell>
            <TableCell align="center">Manage</TableCell>
            <TableCell align="center">Delete</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {cosmosConfigs.map((config) => (
            <TableRow key={config.chainName}>
              <TableCell component="th" scope="row">
                {config.chainName}
              </TableCell>
              <TableCell component="th" scope="row">
                <Box px={2}>
                  <Button onClick={() => {
                    manageConfiguration(COSMOS_SETUP_PAGE, config);
                  }}
                  >
                    Manage
                  </Button>
                </Box>
              </TableCell>
              <TableCell align="center">
                <Button onClick={() => {
                  removeConfigDetails(config);
                }}
                >
                  Delete
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
  pageChanger: PropTypes.func.isRequired,
  loadConfigDetails: PropTypes.func.isRequired,
  removeConfigDetails: PropTypes.func.isRequired,
};

export default CosmosChainsTable;
