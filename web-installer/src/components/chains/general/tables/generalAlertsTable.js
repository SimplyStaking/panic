import React from 'react';
import PropTypes from 'prop-types';
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  FormControlLabel, Checkbox, Typography, TextField, Grid, Box,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import StepButtonContainer from
  '../../../../containers/chains/cosmos/stepButtonContainer';
import NavigationButton from '../../../global/navigationButton';
import {
  CHAINS_PAGE, DONE, BACK, CHANNELS_STEP, CHAINS_STEP,
} from '../../../../constants/constants';

const AlertsTable = (props) => {
  const {
    config,
    currentChain,
    updateThresholdAlertDetails,
  } = props;

  // Assigning buffer values as they become too long
  const ThresholdAlerts = config.byId[currentChain].thresholdAlerts;

  const nextPage = (page) => {
    const {
      pageChanger, stepChanger,
    } = props;

    const payload = {
      step: CHAINS_STEP,
    };

    stepChanger(payload);
    pageChanger({ page });
  };

  return (
    <div>
      <Typography
        style={{ textAlign: 'center' }}
        variant="h5"
        align="center"
        gutterBottom
      >
        Alert Threshold Configuration
      </Typography>
      <Box py={4}>
        <TableContainer component={Paper}>
          <Table aria-label="simple table">
            <TableHead>
              <TableRow>
                <TableCell align="center">Alert</TableCell>
                <TableCell align="center">Warning Threshold</TableCell>
                <TableCell align="center">Critical Threshold</TableCell>
                <TableCell align="center">Enabled</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {ThresholdAlerts.allIds.map((id) => (
                <TableRow key={id}>
                  <TableCell align="center">
                    {ThresholdAlerts.byId[id].name}
                  </TableCell>
                  <TableCell align="center">
                    <Grid container>
                      <Grid item>
                        <FormControlLabel
                          control={(
                            <Checkbox
                              checked={ThresholdAlerts.byId[id].warning.enabled}
                              onClick={() => {
                                updateThresholdAlertDetails(
                                  {
                                    id,
                                    parentId: currentChain,
                                    alert: {
                                      name: ThresholdAlerts.byId[id].name,
                                      warning: {
                                        threshold: ThresholdAlerts.byId[id].warning.threshold,
                                        enabled: !ThresholdAlerts.byId[id].warning.enabled,
                                      },
                                      critical: ThresholdAlerts.byId[id].critical,
                                      enabled: ThresholdAlerts.byId[id].enabled,
                                    },
                                  },
                                );
                              }}
                              color="primary"
                            />
                          )}
                          label="Enabled"
                          labelPlacement="end"
                        />
                      </Grid>
                      <Grid item>
                        <Grid container>
                          <TextField
                            value={ThresholdAlerts.byId[id].warning.threshold}
                            type="text"
                            name="thresholdWarning"
                            label="Threshold"
                            placeholder="60"
                            onChange={(event) => {
                              updateThresholdAlertDetails(
                                {
                                  id,
                                  parentId: currentChain,
                                  alert: {
                                    name: ThresholdAlerts.byId[id].name,
                                    warning: {
                                      threshold: event.target.value,
                                      enabled: ThresholdAlerts.byId[id].warning.enabled,
                                    },
                                    critical: ThresholdAlerts.byId[id].critical,
                                    enabled: ThresholdAlerts.byId[id].enabled,
                                  },
                                },
                              );
                            }}
                            fullWidth
                          />
                        </Grid>
                      </Grid>
                    </Grid>
                  </TableCell>
                  <TableCell align="center">
                    <FormControlLabel
                      control={(
                        <Checkbox
                          checked={ThresholdAlerts.byId[id].critical.enabled}
                          onClick={() => {
                            updateThresholdAlertDetails(
                              {
                                id,
                                parentId: currentChain,
                                alert: {
                                  name: ThresholdAlerts.byId[id].name,
                                  warning: ThresholdAlerts.byId[id].warning,
                                  critical: {
                                    threshold: ThresholdAlerts.byId[id].critical.threshold,
                                    enabled: !ThresholdAlerts.byId[id].critical.enabled,
                                  },
                                  enabled: ThresholdAlerts.byId[id].enabled,
                                },
                              },
                            );
                          }}
                          color="primary"
                        />
                      )}
                      label="Enabled"
                      labelPlacement="end"
                    />
                    <TextField
                      value={ThresholdAlerts.byId[id].critical.threshold}
                      type="text"
                      name="thresholdWarning"
                      label="Threshold"
                      placeholder="60"
                      onChange={(event) => {
                        updateThresholdAlertDetails(
                          {
                            id,
                            parentId: currentChain,
                            alert: {
                              name: ThresholdAlerts.byId[id].name,
                              warning: ThresholdAlerts.byId[id].warning,
                              critical: {
                                threshold: event.target.value,
                                enabled: ThresholdAlerts.byId[id].critical.enabled,
                              },
                              enabled: ThresholdAlerts.byId[id].enabled,
                            },
                          },
                        );
                      }}
                      fullWidth
                    />
                  </TableCell>
                  <TableCell align="center">
                    <FormControlLabel
                      control={(
                        <Checkbox
                          checked={ThresholdAlerts.byId[id].enabled}
                          onClick={() => {
                            updateThresholdAlertDetails({
                              id,
                              parentId: currentChain,
                              alert: {
                                name: ThresholdAlerts.byId[id].name,
                                warning: ThresholdAlerts.byId[id].warning,
                                critical: ThresholdAlerts.byId[id].critical,
                                enabled: !ThresholdAlerts.byId[id].enabled,
                              },
                            });
                          }}
                          name="enabled"
                          color="primary"
                        />
                      )}
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
      <Grid container spacing={2}>
        <Grid item xs={2}>
          <Box px={2}>
            <StepButtonContainer
              disabled={false}
              text={BACK}
              navigation={CHANNELS_STEP}
            />
          </Box>
        </Grid>
        <Grid item xs={8} />
        <Grid item xs={2}>
          <Box px={2}>
            <NavigationButton
              disabled={false}
              nextPage={nextPage}
              buttonText={DONE}
              navigation={CHAINS_PAGE}
            />
          </Box>
        </Grid>
      </Grid>
    </div>
  );
};

AlertsTable.propTypes = {
  pageChanger: PropTypes.func.isRequired,
  stepChanger: PropTypes.func.isRequired,
  config: PropTypes.shape({
    byId: PropTypes.shape({
      thresholdAlerts: PropTypes.shape({
        byId: PropTypes.shape({
          name: PropTypes.string,
          warning: PropTypes.shape({
            threshold: PropTypes.number,
            enabled: PropTypes.bool,
          }),
          critical: PropTypes.shape({
            threshold: PropTypes.number,
            enabled: PropTypes.bool,
          }),
          enabled: PropTypes.bool,
        }),
        allIds: [],
      }),
    }).isRequired,
  }).isRequired,
  updateThresholdAlertDetails: PropTypes.func.isRequired,
  currentChain: PropTypes.string.isRequired,
};

export default AlertsTable;
