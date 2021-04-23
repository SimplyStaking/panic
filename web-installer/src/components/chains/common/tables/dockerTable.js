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

const DockerTable = ({
  currentChain,
  config,
  dockerConfig,
  removeDockerDetails,
}) => {
  if (config.byId[currentChain].dockers.length === 0) {
    return <div />;
  }
  return (
    <TableContainer component={Paper}>
      <Table className="table" aria-label="simple table" style={{ marginBottom: '150px' }}>
        <TableHead>
          <TableRow>
            <TableCell align="center">Name</TableCell>
            <TableCell align="center">Monitor</TableCell>
            <TableCell align="center">Delete</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {config.byId[currentChain].dockers.map((id) => (
            <TableRow key={id}>
              <TableCell align="center">
                {dockerConfig.byId[id].name}
              </TableCell>
              <TableCell align="center">
                {dockerConfig.byId[id].monitor_docker ? (
                  <CheckIcon />
                ) : (
                  <ClearIcon />
                )}
              </TableCell>
              <TableCell align="center">
                <Button
                  onClick={() => {
                    removeDockerDetails({
                      id: dockerConfig.byId[id].id,
                      parent_id: currentChain,
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
    </TableContainer>
  );
};

DockerTable.propTypes = forbidExtraProps({
  config: PropTypes.shape({
    byId: PropTypes.shape({
      dockers: PropTypes.arrayOf(PropTypes.string),
    }).isRequired,
  }).isRequired,
  dockerConfig: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      parent_id: PropTypes.string,
      name: PropTypes.string,
      monitor_docker: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  removeDockerDetails: PropTypes.func.isRequired,
  currentChain: PropTypes.string.isRequired,
});

export default DockerTable;
