import React from 'react';
import PropTypes from 'prop-types';
import {
  Table, TableBody, TableContainer, TableHead, TableRow, FormControlLabel,
  Checkbox, Typography, Grid, Box,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import StepButtonContainer from 'containers/chains/common/stepButtonContainer';
import NavigationButton from 'components/global/navigationButton';
import {
  DONE, BACK, CHANNELS_STEP, CHAINS_STEP, CHAINS_PAGE,
} from 'constants/constants';
import { MuiThemeProvider } from '@material-ui/core/styles';
import { defaultTheme } from 'components/theme/default';
import useStyles from 'assets/jss/material-kit-react/views/landingPageSections/productStyle';

import InputAdornment from '@material-ui/core/InputAdornment';
import GridContainer from 'components/material_ui/Grid/GridContainer';
import GridItem from 'components/material_ui/Grid/GridItem';
import Data from 'data/alert';
import StyledTableRow from 'assets/jss/custom-jss/StyledTableRow';
import StyledTableCell from 'assets/jss/custom-jss/StyledTableCell';
import CssTextField from 'assets/jss/custom-jss/CssTextField';

/*
 * AlertsTable will show display the alert types needed for general
 * configuration together with the function to directly edit them.
 */

const AlertsTable = ({
  config,
  currentChain,
  updateThresholdAlertDetails,
  pageChanger,
  stepChanger,
}) => {
  // Assigning buffer values as they become too long
  const ThresholdAlerts = config.byId[currentChain].thresholdAlerts;

  const nextPage = (page) => {
    const payload = {
      step: CHAINS_STEP,
    };

    stepChanger(payload);
    pageChanger({ page });
  };

  const classes = useStyles();

  return (
    <MuiThemeProvider theme={defaultTheme}>
      <div>
        <div className={classes.subsection}>
          <GridContainer justify="center">
            <GridItem xs={12} sm={12} md={8}>
              <h1 className={classes.title}>{Data.title}</h1>
            </GridItem>
          </GridContainer>
        </div>
        <Typography variant="subtitle1" gutterBottom className="greyBackground">
          <Box m={2} p={3}>
            <p>{Data.description}</p>
          </Box>
        </Typography>
        <div className={classes.subsection}>
          <GridContainer justify="center">
            <GridItem xs={12} sm={12} md={8}>
              <h1 className={classes.title}>{Data.subtitle_1}</h1>
            </GridItem>
          </GridContainer>
        </div>
        <Box py={4}>
          <TableContainer component={Paper}>
            <Table aria-label="general-alerts-table" style={{ tableLayout: 'fixed' }}>
              <TableHead>
                <TableRow>
                  <StyledTableCell align="left">Alert</StyledTableCell>
                  <StyledTableCell align="center">Warning Threshold</StyledTableCell>
                  <StyledTableCell align="center">Critical Threshold</StyledTableCell>
                  <StyledTableCell align="center">Enabled</StyledTableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {ThresholdAlerts.allIds.map((id) => (
                  <StyledTableRow key={id}>
                    <StyledTableCell align="left">
                      <h4>
                        <b>{ThresholdAlerts.byId[id].name}</b>
                      </h4>
                      <p>{ThresholdAlerts.byId[id].description}</p>
                    </StyledTableCell>
                    <StyledTableCell align="center">
                      <Grid container spacing={1} justify="flex-end" alignItems="flex-end">
                        <Grid item>
                          <FormControlLabel
                            control={(
                              <Checkbox
                                checked={
                                  ThresholdAlerts.byId[id].warning.enabled
                                }
                                onClick={() => {
                                  updateThresholdAlertDetails({
                                    id,
                                    parent_id: currentChain,
                                    alert: {
                                      name: ThresholdAlerts.byId[id].name,
                                      identifier:
                                        ThresholdAlerts.byId[id].identifier,
                                      description:
                                        ThresholdAlerts.byId[id].description,
                                      adornment:
                                        ThresholdAlerts.byId[id].adornment,
                                      adornment_time:
                                        ThresholdAlerts.byId[id].adornment_time,
                                      warning: {
                                        threshold:
                                          ThresholdAlerts.byId[id].warning
                                            .threshold,
                                        enabled: !ThresholdAlerts.byId[id]
                                          .warning.enabled,
                                      },
                                      critical:
                                        ThresholdAlerts.byId[id].critical,
                                      enabled: ThresholdAlerts.byId[id].enabled,
                                    },
                                  });
                                }}
                                color="primary"
                              />
                            )}
                            label="Enabled"
                            labelPlacement="end"
                          />
                        </Grid>
                        <Grid item>
                          <CssTextField
                            id={('threshold-warning-outlined-full-width-'.concat(id))}
                            value={ThresholdAlerts.byId[id].warning.threshold}
                            label="Threshold"
                            type="text"
                            style={{ margin: 8 }}
                            name="thresholdWarning"
                            placeholder="60"
                            onChange={(event) => {
                              updateThresholdAlertDetails({
                                id,
                                parent_id: currentChain,
                                alert: {
                                  name: ThresholdAlerts.byId[id].name,
                                  identifier:
                                    ThresholdAlerts.byId[id].identifier,
                                  description:
                                    ThresholdAlerts.byId[id].description,
                                  adornment:
                                    ThresholdAlerts.byId[id].adornment,
                                  adornment_time:
                                    ThresholdAlerts.byId[id].adornment_time,
                                  warning: {
                                    threshold: event.target.value,
                                    enabled:
                                      ThresholdAlerts.byId[id].warning
                                        .enabled,
                                  },
                                  critical: ThresholdAlerts.byId[id].critical,
                                  enabled: ThresholdAlerts.byId[id].enabled,
                                },
                              });
                            }}
                            inputProps={{
                              min: 0,
                              style: { textAlign: 'right' },
                            }}
                            variant="outlined"
                            autoComplete="off"
                            /* eslint-disable-next-line react/jsx-no-duplicate-props */
                            InputProps={{
                              endAdornment: (
                                <InputAdornment position="end">
                                  {ThresholdAlerts.byId[id].adornment}
                                </InputAdornment>
                              ),
                            }}
                            fullWidth
                          />
                        </Grid>
                      </Grid>
                    </StyledTableCell>
                    <StyledTableCell align="center">
                      <Grid container spacing={1} justify="flex-end" alignItems="flex-end">
                        <Grid item>
                          <FormControlLabel
                            control={(
                              <Checkbox
                                checked={
                                  ThresholdAlerts.byId[id].critical.enabled
                                }
                                onClick={() => {
                                  updateThresholdAlertDetails({
                                    id,
                                    parent_id: currentChain,
                                    alert: {
                                      name: ThresholdAlerts.byId[id].name,
                                      identifier:
                                        ThresholdAlerts.byId[id].identifier,
                                      description:
                                        ThresholdAlerts.byId[id].description,
                                      adornment:
                                        ThresholdAlerts.byId[id].adornment,
                                      adornment_time:
                                        ThresholdAlerts.byId[id].adornment_time,
                                      warning: ThresholdAlerts.byId[id].warning,
                                      critical: {
                                        threshold:
                                          ThresholdAlerts.byId[id].critical
                                            .threshold,
                                        enabled: !ThresholdAlerts.byId[id]
                                          .critical.enabled,
                                      },
                                      enabled: ThresholdAlerts.byId[id].enabled,
                                    },
                                  });
                                }}
                                color="primary"
                              />
                            )}
                            label="Enabled"
                            labelPlacement="end"
                          />
                        </Grid>
                        <Grid item>
                          <CssTextField
                            id={('threshold-critical-threshold-outlined-full-width-'.concat(id))}
                            value={
                              ThresholdAlerts.byId[id].critical.threshold
                            }
                            label="Threshold"
                            type="text"
                            style={{ margin: 8 }}
                            name="thresholdCritical"
                            placeholder="60"
                            onChange={(event) => {
                              updateThresholdAlertDetails({
                                id,
                                parent_id: currentChain,
                                alert: {
                                  name: ThresholdAlerts.byId[id].name,
                                  identifier:
                                    ThresholdAlerts.byId[id].identifier,
                                  description:
                                    ThresholdAlerts.byId[id].description,
                                  adornment:
                                    ThresholdAlerts.byId[id].adornment,
                                  adornment_time:
                                    ThresholdAlerts.byId[id].adornment_time,
                                  warning: ThresholdAlerts.byId[id].warning,
                                  critical: {
                                    threshold: event.target.value,
                                    repeat:
                                      ThresholdAlerts.byId[id].critical
                                        .repeat,
                                    enabled:
                                      ThresholdAlerts.byId[id].critical
                                        .enabled,
                                  },
                                  enabled: ThresholdAlerts.byId[id].enabled,
                                },
                              });
                            }}
                            variant="outlined"
                            inputProps={{
                              min: 0,
                              style: { textAlign: 'right' },
                            }}
                            autoComplete="off"
                            /* eslint-disable-next-line react/jsx-no-duplicate-props */
                            InputProps={{
                              endAdornment: (
                                <InputAdornment position="end">
                                  {ThresholdAlerts.byId[id].adornment}
                                </InputAdornment>
                              ),
                            }}
                            fullWidth
                          />
                        </Grid>
                        <Grid item>
                          <CssTextField
                            id={('threshold-critical-repeat-outlined-full-width-'.concat(id))}
                            value={ThresholdAlerts.byId[id].critical.repeat}
                            label="Repeat"
                            type="text"
                            style={{ margin: 8 }}
                            name="thresholdCritical"
                            placeholder="60"
                            onChange={(event) => {
                              updateThresholdAlertDetails({
                                id,
                                parent_id: currentChain,
                                alert: {
                                  name: ThresholdAlerts.byId[id].name,
                                  identifier:
                                    ThresholdAlerts.byId[id].identifier,
                                  description:
                                    ThresholdAlerts.byId[id].description,
                                  adornment:
                                    ThresholdAlerts.byId[id].adornment,
                                  adornment_time:
                                    ThresholdAlerts.byId[id].adornment_time,
                                  warning: ThresholdAlerts.byId[id].warning,
                                  critical: {
                                    threshold:
                                      ThresholdAlerts.byId[id].critical
                                        .threshold,
                                    repeat: event.target.value,
                                    enabled:
                                      ThresholdAlerts.byId[id].critical
                                        .enabled,
                                  },
                                  enabled: ThresholdAlerts.byId[id].enabled,
                                },
                              });
                            }}
                            variant="outlined"
                            inputProps={{
                              min: 0,
                              style: { textAlign: 'right' },
                            }}
                            autoComplete="off"
                            /* eslint-disable-next-line react/jsx-no-duplicate-props */
                            InputProps={{
                              endAdornment: (
                                <InputAdornment position="end">
                                  {ThresholdAlerts.byId[id].adornment_time}
                                </InputAdornment>
                              ),
                            }}
                            fullWidth
                          />
                        </Grid>
                      </Grid>
                    </StyledTableCell>
                    <StyledTableCell align="center">
                      <FormControlLabel
                        control={(
                          <Checkbox
                            checked={ThresholdAlerts.byId[id].enabled}
                            onClick={() => {
                              updateThresholdAlertDetails({
                                id,
                                parent_id: currentChain,
                                alert: {
                                  name: ThresholdAlerts.byId[id].name,
                                  identifier:
                                    ThresholdAlerts.byId[id].identifier,
                                  description:
                                    ThresholdAlerts.byId[id].description,
                                  adornment: ThresholdAlerts.byId[id].adornment,
                                  adornment_time:
                                    ThresholdAlerts.byId[id].adornment_time,
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
                        label=""
                      />
                    </StyledTableCell>
                  </StyledTableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
        <Grid container spacing={2}>
          <Grid item xs={12} />
          <br />
          <br />
          <Grid item xs={4} />
          <Grid item xs={2}>
            <Box px={2}>
              <StepButtonContainer
                disabled={false}
                text={BACK}
                navigation={CHANNELS_STEP}
              />
            </Box>
          </Grid>
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
          <Grid item xs={4} />
          <Grid item xs={12} />
        </Grid>
      </div>
    </MuiThemeProvider>
  );
};

AlertsTable.propTypes = {
  pageChanger: PropTypes.func.isRequired,
  stepChanger: PropTypes.func.isRequired,
  config: PropTypes.shape({
    byId: PropTypes.shape({
      repeatAlerts: PropTypes.shape({
        byId: PropTypes.shape({
          name: PropTypes.string,
          description: PropTypes.string,
          warning: PropTypes.shape({
            repeat: PropTypes.number,
            enabled: PropTypes.bool,
          }),
          critical: PropTypes.shape({
            repeat: PropTypes.number,
            enabled: PropTypes.bool,
          }),
          enabled: PropTypes.bool,
        }),
        allIds: PropTypes.arrayOf(PropTypes.string),
      }),
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
        allIds: PropTypes.arrayOf(PropTypes.string),
      }),
    }).isRequired,
  }).isRequired,
  updateThresholdAlertDetails: PropTypes.func.isRequired,
  currentChain: PropTypes.string.isRequired,
};

export default AlertsTable;
