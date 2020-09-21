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
    cosmosConfigs,
    // loadConfigDetails,
    removeConfigDetails,
  } = props;

  // const manageConfiguration = (page, config) => {
  //   const { pageChanger } = props;
  //   pageChanger({ page });
  //   loadConfigDetails(config);
  // };

  if (cosmosConfigs.length === 0) {
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
          {cosmosConfigs.map((config) => (
            <TableRow key={config.chainName}>
              <TableCell component="th" scope="row">
                {config.chainName}
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
                  removeConfigDetails(config);
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
  // loadConfigDetails: PropTypes.func.isRequired,
  removeConfigDetails: PropTypes.func.isRequired,
};

export default CosmosChainsTable;
