import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import {
  Table, TableBody, TableContainer, TableHead, TableRow, Button,
  Box, Typography,
} from '@material-ui/core';
import CancelIcon from '@material-ui/icons/Cancel';
import Paper from '@material-ui/core/Paper';
import { COSMOS_SETUP_PAGE } from 'constants/constants';
import StyledTableRow from 'assets/jss/custom-jss/StyledTableRow';
import StyledTableCell from 'assets/jss/custom-jss/StyledTableCell';

/*
 * Displays all the names of the configured chains, in the chain accordion.
 * Has functionality to load a chains configuration as well as clear all data
 * setup for a chain.
 */
const CosmosChainsTable = ({
  config,
  loadConfigDetails,
  pageChanger,
  removeChainDetails,
  removeNodeDetails,
  removeRepositoryDetails,
  removeSlackDetails,
  removeDockerDetails,
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
    let telegramPayload = {};
    let twilioPayload = {};
    let emailPayload = {};
    let opsGeniePayload = {};
    let pagerDutyPayload = {};
    let slackPayload = {};
    let index = 0;

    for (let i = 0; i < telegrams.allIds.length; i += 1) {
      telegramPayload = JSON.parse(JSON.stringify(telegrams.byId[telegrams.allIds[i]]));
      if (telegramPayload.parent_ids.includes(chainID)) {
        index = telegramPayload.parent_ids.indexOf(chainID);
        if (index > -1) {
          telegramPayload.parent_ids.splice(index, 1);
        }
        index = telegramPayload.parent_names.indexOf(currentConfig.chain_name);
        if (index > -1) {
          telegramPayload.parent_names.splice(index, 1);
        }
        removeTelegramDetails(telegramPayload);
      }
    }

    for (let i = 0; i < twilios.allIds.length; i += 1) {
      twilioPayload = JSON.parse(JSON.stringify(twilios.byId[twilios.allIds[i]]));
      if (twilioPayload.parent_ids.includes(chainID)) {
        index = twilioPayload.parent_ids.indexOf(chainID);
        if (index > -1) {
          twilioPayload.parent_ids.splice(index, 1);
        }
        index = twilioPayload.parent_names.indexOf(currentConfig.chain_name);
        if (index > -1) {
          twilioPayload.parent_names.splice(index, 1);
        }
        removeTwilioDetails(twilioPayload);
      }
    }

    for (let i = 0; i < emails.allIds.length; i += 1) {
      emailPayload = JSON.parse(JSON.stringify(emails.byId[emails.allIds[i]]));
      if (emailPayload.parent_ids.includes(chainID)) {
        index = emailPayload.parent_ids.indexOf(chainID);
        if (index > -1) {
          emailPayload.parent_ids.splice(index, 1);
        }
        index = emailPayload.parent_names.indexOf(currentConfig.chain_name);
        if (index > -1) {
          emailPayload.parent_names.splice(index, 1);
        }
        removeEmailDetails(emailPayload);
      }
    }

    for (let i = 0; i < opsgenies.allIds.length; i += 1) {
      opsGeniePayload = JSON.parse(JSON.stringify(opsgenies.byId[opsgenies.allIds[i]]));
      if (opsGeniePayload.parent_ids.includes(chainID)) {
        index = opsGeniePayload.parent_ids.indexOf(chainID);
        if (index > -1) {
          opsGeniePayload.parent_ids.splice(index, 1);
        }
        index = opsGeniePayload.parent_names.indexOf(currentConfig.chain_name);
        if (index > -1) {
          opsGeniePayload.parent_names.splice(index, 1);
        }
        removeOpsGenieDetails(opsGeniePayload);
      }
    }

    for (let i = 0; i < pagerduties.allIds.length; i += 1) {
      pagerDutyPayload = JSON.parse(JSON.stringify(pagerduties.byId[pagerduties.allIds[i]]));
      if (pagerDutyPayload.parent_ids.includes(chainID)) {
        index = pagerDutyPayload.parent_ids.indexOf(chainID);
        if (index > -1) {
          pagerDutyPayload.parent_ids.splice(index, 1);
        }
        index = pagerDutyPayload.parent_names.indexOf(currentConfig.chain_name);
        if (index > -1) {
          pagerDutyPayload.parent_names.splice(index, 1);
        }
        removePagerDutyDetails(pagerDutyPayload);
      }
    }

    for (let i = 0; i < slacks.allIds.length; i += 1) {
      slackPayload = JSON.parse(JSON.stringify(slacks.byId[slacks.allIds[i]]));
      if (slackPayload.parent_ids.includes(chainID)) {
        index = slackPayload.parent_ids.indexOf(chainID);
        if (index > -1) {
          slackPayload.parent_ids.splice(index, 1);
        }
        index = slackPayload.parent_names.indexOf(currentConfig.chain_name);
        if (index > -1) {
          slackPayload.parent_names.splice(index, 1);
        }
        removeSlackDetails(slackPayload);
      }
    }

    // Clear all the configured dockers from state
    for (let i = 0; i < currentConfig.dockers.length; i += 1) {
      payload.id = currentConfig.dockers[i];
      removeDockerDetails(payload);
    }

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
    // Finally clear the chain from the configuration
    payload.id = chainID;
    removeChainDetails(payload);
  }

  if (config.allIds.length === 0) {
    return <div />;
  }
  return (
    <TableContainer component={Paper}>
      <Table className="table" aria-label="cosmos-chains-table">
        <TableHead>
          <TableRow>
            <StyledTableCell align="center">Chain Name</StyledTableCell>
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
                      loadConfiguration(COSMOS_SETUP_PAGE, id);
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

CosmosChainsTable.propTypes = forbidExtraProps({
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
  removeDockerDetails: PropTypes.func.isRequired,
});

export default CosmosChainsTable;
