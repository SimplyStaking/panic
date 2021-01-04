import React from 'react';
import PropTypes from 'prop-types';
import forbidExtraProps from 'airbnb-prop-types';
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

const RepositoriesTable = ({
  currentChain,
  config,
  reposConfig,
  removeRepositoryDetails,
}) => {
  if (config.byId[currentChain].repositories.length === 0) {
    return <div />;
  }
  return (
    <TableContainer component={Paper}>
      <Table className="table" aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell align="center">Name</TableCell>
            <TableCell align="center">Monitor</TableCell>
            <TableCell align="center">Delete</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {config.byId[currentChain].repositories.map((id) => (
            <TableRow key={id}>
              <TableCell align="center">
                {reposConfig.byId[id].repo_name}
              </TableCell>
              <TableCell align="center">
                {reposConfig.byId[id].monitor_repo ? (
                  <CheckIcon />
                ) : (
                  <ClearIcon />
                )}
              </TableCell>
              <TableCell align="center">
                <Button
                  onClick={() => {
                    removeRepositoryDetails({
                      id: reposConfig.byId[id].id,
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
      <br />
      <br />
      <br />
    </TableContainer>
  );
};

RepositoriesTable.propTypes = forbidExtraProps({
  config: PropTypes.shape({
    byId: PropTypes.shape({
      repositories: PropTypes.arrayOf(PropTypes.string),
    }).isRequired,
  }).isRequired,
  reposConfig: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      parent_id: PropTypes.string,
      repo_name: PropTypes.string,
      monitor_repo: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  removeRepositoryDetails: PropTypes.func.isRequired,
  currentChain: PropTypes.string.isRequired,
});

export default RepositoriesTable;
