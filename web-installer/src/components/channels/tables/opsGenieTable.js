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

const OpsGenieTable = ({ opsGenies, removeOpsGenieDetails }) => {
  if (opsGenies.allIds.length === 0) {
    return <div />;
  }
  return (
    <TableContainer component={Paper}>
      <Table className="greyBackground" aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell align="center">Name</TableCell>
            <TableCell align="center">API Token</TableCell>
            <TableCell align="center">EU</TableCell>
            <TableCell align="center">Info</TableCell>
            <TableCell align="center">Warning</TableCell>
            <TableCell align="center">Critical</TableCell>
            <TableCell align="center">Error</TableCell>
            <TableCell align="center">Delete</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {Object.keys(opsGenies.byId).map((opsgenie) => (
            <TableRow key={opsGenies.byId[opsgenie].id}>
              <TableCell align="center">
                {opsGenies.byId[opsgenie].channel_name}
              </TableCell>
              <TableCell align="center">
                {opsGenies.byId[opsgenie].api_token}
              </TableCell>
              <TableCell align="center">
                {opsGenies.byId[opsgenie].eu ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                {opsGenies.byId[opsgenie].info ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                {opsGenies.byId[opsgenie].warning ? (
                  <CheckIcon />
                ) : (
                  <ClearIcon />
                )}
              </TableCell>
              <TableCell align="center">
                {opsGenies.byId[opsgenie].critical ? (
                  <CheckIcon />
                ) : (
                  <ClearIcon />
                )}
              </TableCell>
              <TableCell align="center">
                {opsGenies.byId[opsgenie].error ? <CheckIcon /> : <ClearIcon />}
              </TableCell>
              <TableCell align="center">
                <Button
                  onClick={() => {
                    removeOpsGenieDetails(opsGenies.byId[opsgenie]);
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

OpsGenieTable.propTypes = forbidExtraProps({
  opsGenies: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      channel_name: PropTypes.string,
      api_token: PropTypes.string,
      eu: PropTypes.bool,
      info: PropTypes.bool,
      warning: PropTypes.bool,
      critical: PropTypes.bool,
      error: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  removeOpsGenieDetails: PropTypes.func.isRequired,
});

export default OpsGenieTable;
