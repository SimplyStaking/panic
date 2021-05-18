import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import {
  Table,
  TableBody,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Box,
  Grid,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import CheckIcon from '@material-ui/icons/Check';
import ClearIcon from '@material-ui/icons/Clear';
import CancelIcon from '@material-ui/icons/Cancel';
import StyledTableRow from 'assets/jss/custom-jss/StyledTableRow';
import StyledTableCell from 'assets/jss/custom-jss/StyledTableCell';
import StepButtonContainer from 'containers/chains/common/stepButtonContainer';
import NavigationButton from 'components/global/navigationButton';
import { NEXT, BACK, GENERAL } from 'constants/constants';

const SystemTable = ({
  currentChain,
  config,
  systemConfig,
  removeSystemDetails,
  data,
  pageChanger,
}) => {
  // Next page is in fact returning back to the Chains Settings Page
  // but keeping the name the same for consistency
  function nextPage(page) {
    // Clear the current chain, id we are working on.
    pageChanger({ page });
  }

  if (config.byId[currentChain].systems.length === 0) {
    return (
      <div>
        <Box py={4}>
          <Grid container spacing={3} justify="center" alignItems="center">
            <Grid item xs={4} />
            <Grid item xs={2}>
              {currentChain === GENERAL ? (
                <NavigationButton
                  disabled={false}
                  nextPage={nextPage}
                  buttonText={BACK}
                  navigation={data.systemForm.backStep}
                />
              ) : (
                <StepButtonContainer
                  disabled={false}
                  text={BACK}
                  navigation={data.systemForm.backStep}
                />
              )}
            </Grid>
            <Grid item xs={2}>
              <StepButtonContainer
                disabled={false}
                text={NEXT}
                navigation={data.systemForm.nextStep}
              />
            </Grid>
            <Grid item xs={4} />
          </Grid>
        </Box>
      </div>
    );
  }

  return (
    <Box pt={5}>
      <TableContainer component={Paper}>
        <Table className="table" aria-label="systems table">
          <TableHead>
            <TableRow>
              <StyledTableCell align="center">Name</StyledTableCell>
              <StyledTableCell align="center">Node Exporter Url</StyledTableCell>
              <StyledTableCell align="center">Monitor</StyledTableCell>
              <StyledTableCell align="center">Delete</StyledTableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {config.byId[currentChain].systems.map((id) => (
              <StyledTableRow key={id}>
                <StyledTableCell align="center">{systemConfig.byId[id].name}</StyledTableCell>
                <StyledTableCell align="center">
                  {systemConfig.byId[id].exporter_url}
                </StyledTableCell>
                <StyledTableCell align="center">
                  {systemConfig.byId[id].monitor_system ? <CheckIcon /> : <ClearIcon />}
                </StyledTableCell>
                <StyledTableCell align="center">
                  <Button
                    onClick={() => {
                      removeSystemDetails({
                        id: systemConfig.byId[id].id,
                        parent_id: currentChain,
                      });
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
      <Box py={4}>
        <Grid container spacing={3} justify="center" alignItems="center">
          <Grid item xs={4} />
          <Grid item xs={2}>
            {currentChain === GENERAL ? (
              <NavigationButton
                disabled={false}
                nextPage={nextPage}
                buttonText={BACK}
                navigation={data.systemForm.backStep}
              />
            ) : (
              <StepButtonContainer
                disabled={false}
                text={BACK}
                navigation={data.systemForm.backStep}
              />
            )}
          </Grid>
          <Grid item xs={2}>
            <StepButtonContainer
              disabled={false}
              text={NEXT}
              navigation={data.systemForm.nextStep}
            />
          </Grid>
          <Grid item xs={4} />
        </Grid>
      </Box>
    </Box>
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
  currentChain: PropTypes.string.isRequired,
  pageChanger: PropTypes.func.isRequired,
  data: PropTypes.shape({
    systemForm: PropTypes.shape({
      backStep: PropTypes.string.isRequired,
      nextStep: PropTypes.string.isRequired,
    }).isRequired,
  }).isRequired,
});

export default SystemTable;
