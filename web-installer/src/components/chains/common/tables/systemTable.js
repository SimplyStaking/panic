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
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import CheckIcon from '@material-ui/icons/Check';
import ClearIcon from '@material-ui/icons/Clear';
import CancelIcon from '@material-ui/icons/Cancel';
import { GLOBAL } from 'constants/constants';

const SystemTable = ({ config, systemConfig, removeSystemDetails }) => {
  const currentConfig = config.byId[GLOBAL];

  if (currentConfig.systems.length === 0) {
    return <div />;
  }
  return (
    <TableContainer component={Paper}>
      <Table className="table" aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell align="center">Name</TableCell>
            <TableCell align="center">Node Exporter Url</TableCell>
            <TableCell align="center">Monitor</TableCell>
            <TableCell align="center">Delete</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {currentConfig.systems.map((id) => (
            <TableRow key={id}>
              <TableCell align="center">{systemConfig.byId[id].name}</TableCell>
              <TableCell align="center">
                {systemConfig.byId[id].exporter_url}
              </TableCell>
              <TableCell align="center">
                {systemConfig.byId[id].monitor_system ? (
                  <CheckIcon />
                ) : (
                  <ClearIcon />
                )}
              </TableCell>
              <TableCell align="center">
                <Button
                  onClick={() => {
                    removeSystemDetails({
                      id: systemConfig.byId[id].id,
                      parent_id: GLOBAL,
                    });
                  }}
                >
                  <CancelIcon />
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <br />
      <br />
      <br />
    </TableContainer>
  );
};

SystemTable.propTypes = forbidExtraProps({
  config: PropTypes.shape({
    byId: PropTypes.shape({
      systems: PropTypes.arrayOf(PropTypes.string),
    }).isRequired,
  }).isRequired,
  systemConfig: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      parent_id: PropTypes.string,
      name: PropTypes.string,
      exporter_url: PropTypes.string,
      monitor_system: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  removeSystemDetails: PropTypes.func.isRequired,
});

export default SystemTable;
