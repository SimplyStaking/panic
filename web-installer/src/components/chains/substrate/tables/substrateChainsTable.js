import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import {
  Table, TableBody, TableContainer, TableHead, TableRow, Button,
  Box, Typography,
} from '@material-ui/core';
import CancelIcon from '@material-ui/icons/Cancel';
import Paper from '@material-ui/core/Paper';
import { SUBSTRATE_SETUP_PAGE } from 'constants/constants';
import StyledTableRow from 'assets/jss/custom-jss/StyledTableRow';
import StyledTableCell from 'assets/jss/custom-jss/StyledTableCell';
import { clearDataSources, clearChannelData } from 'utils/helpers';

const SubstrateChainsTable = ({
  config,
  loadConfigDetails,
  pageChanger,
  removeChainDetails,
  removeNodeDetails,
  removeSlackDetails,
  removeDockerHubDetails,
  removeRepositoryDetails,
  removeOpsGenieDetails,
  removePagerDutyDetails,
  removeEmailDetails,
  removeTwilioDetails,
  removeTelegramDetails,
  telegrams,
  twilios,
  emails,
  pagerduties,
  opsgenies,
  slacks,
}) => {
  const loadConfiguration = (page, id) => {
    loadConfigDetails({ id });
    pageChanger({ page });
  };

  // We have to clean up all the other reducers once a chain configuration
  // is completely removed
  function clearAllChainDetails(chainID) {
    // Assign buffer variable for easier readability
    const currentConfig = config.byId[chainID];
    const payload = { parent_id: chainID, id: '' };

    // Remove all channels
    clearChannelData(currentConfig, telegrams, chainID, removeTelegramDetails);
    clearChannelData(currentConfig, slacks, chainID, removeSlackDetails);
    clearChannelData(currentConfig, twilios, chainID, removeTwilioDetails);
    clearChannelData(currentConfig, emails, chainID, removeEmailDetails);
    clearChannelData(currentConfig, opsgenies, chainID, removeOpsGenieDetails);
    clearChannelData(currentConfig, pagerduties, chainID, removePagerDutyDetails);

    // Remove all data source data
    clearDataSources(currentConfig, 'nodes', removeNodeDetails, payload);
    clearDataSources(currentConfig, 'githubRepositories', removeRepositoryDetails, payload);
    clearDataSources(currentConfig, 'dockerHubs', removeDockerHubDetails, payload);

    // Finally clear the chain from the configuration
    payload.id = chainID;
    removeChainDetails(payload);
  }

  if (config.allIds.length === 0) {
    return <div />;
  }
  return (
    <TableContainer component={Paper}>
      <Table className="table" aria-label="substrate-chains-table">
        <TableHead>
          <TableRow>
            <StyledTableCell align="center">Name</StyledTableCell>
            <StyledTableCell align="center">Edit/View Config</StyledTableCell>
            <StyledTableCell align="center">Delete</StyledTableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {config.allIds.map((id) => (
            <StyledTableRow key={id}>
              <StyledTableCell align="center">
                <Typography variant="h6" style={{ fontWeight: '450' }}>
                  {config.byId[id].chain_name}
                </Typography>
              </StyledTableCell>
              <StyledTableCell align="center">
                <Box px={2}>
                  <Button
                    variant="contained"
                    onClick={() => {
                      loadConfiguration(SUBSTRATE_SETUP_PAGE, id);
                    }}
                  >
                    Load Chain
                  </Button>
                </Box>
              </StyledTableCell>
              <StyledTableCell align="center">
                <Button
                  onClick={() => {
                    clearAllChainDetails(id);
                  }}
                >
                  <CancelIcon />
                </Button>
              </StyledTableCell>
            </StyledTableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

SubstrateChainsTable.propTypes = forbidExtraProps({
  telegrams: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      channel_name: PropTypes.string,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  twilios: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      channel_name: PropTypes.string,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  emails: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      channel_name: PropTypes.string,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  pagerduties: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      channel_name: PropTypes.string,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  opsgenies: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      channel_name: PropTypes.string,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  config: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      chain_name: PropTypes.string,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string.isRequired).isRequired,
  }).isRequired,
  slacks: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      channel_name: PropTypes.string,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  removeChainDetails: PropTypes.func.isRequired,
  loadConfigDetails: PropTypes.func.isRequired,
  pageChanger: PropTypes.func.isRequired,
  removeNodeDetails: PropTypes.func.isRequired,
  removeRepositoryDetails: PropTypes.func.isRequired,
  removeOpsGenieDetails: PropTypes.func.isRequired,
  removePagerDutyDetails: PropTypes.func.isRequired,
  removeEmailDetails: PropTypes.func.isRequired,
  removeTwilioDetails: PropTypes.func.isRequired,
  removeTelegramDetails: PropTypes.func.isRequired,
  removeSlackDetails: PropTypes.func.isRequired,
  removeDockerHubDetails: PropTypes.func.isRequired,
});

export default SubstrateChainsTable;
