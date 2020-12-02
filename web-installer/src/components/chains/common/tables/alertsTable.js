import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  FormControlLabel, Checkbox, Typography, TextField, Grid, Box, MenuItem,
  Select, FormControl,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import StepButtonContainer from 'containers/chains/common/stepButtonContainer';
import NavigationButton from 'components/global/navigationButton';
import { CHAINS_PAGE, DONE, BACK, CHANNELS_STEP, CHAINS_STEP } from 'constants/constants';
import { MuiThemeProvider } from '@material-ui/core/styles';
import { defaultTheme } from 'components/theme/default';
import styles from "assets/jss/material-kit-react/views/landingPageSections/productStyle.js";
import { makeStyles } from "@material-ui/core/styles";
import InputAdornment from '@material-ui/core/InputAdornment';
import GridContainer from "components/material_ui/Grid/GridContainer.js";
import GridItem from "components/material_ui/Grid/GridItem.js";
import Divider from '@material-ui/core/Divider';
import Data from 'data/alert';

/*
 * AlertsTable will show display all the 4 alert types together with the
 * functions to directly edit them.
*/
const useStyles = makeStyles(styles);

const AlertsTable = ({config, currentChain, updateRepeatAlertDetails,
  updateTimeWindowAlertDetails, updateThresholdAlertDetails,
  updateSeverityAlertDetails, pageChanger, stepChanger, clearChainId}) => {

  // Assigning buffer values as they become too long
  const RepeatAlerts = config.byId[currentChain].repeatAlerts;
  const TimeWindowAlerts = config.byId[currentChain].timeWindowAlerts;
  const ThresholdAlerts = config.byId[currentChain].thresholdAlerts;
  const SeverityAlerts = config.byId[currentChain].severityAlerts;

  const nextPage = (page) => {
    const payload = {
      step: CHAINS_STEP,
    };

    stepChanger(payload);
    pageChanger({ page });
    clearChainId();
  };

  const classes = useStyles();

  return (
    <MuiThemeProvider theme={defaultTheme}>
      <div>
        <div className={classes.subsection}>
          <GridContainer justify="center">
            <GridItem xs={12} sm={12} md={8}>
              <h1 className={classes.title}>
                {Data.title}
              </h1>
            </GridItem>
          </GridContainer>
        </div>
        <Typography variant="subtitle1" gutterBottom className="greyBackground">
          <Box m={2} p={3}>
            <p>{Data.description}</p>
          </Box>
        </Typography>
        <Divider />
        <div className={classes.subsection}>
          <GridContainer justify="center">
            <GridItem xs={12} sm={12} md={8}>
              <h1 className={classes.title}>
                {Data.subtitle_1}
              </h1>
            </GridItem>
          </GridContainer>
        </div>
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
                {RepeatAlerts.allIds.map((id) => (
                  <TableRow key={id}>
                    <TableCell align="center">
                      <h4><b>{RepeatAlerts.byId[id].name}</b></h4>
                      <p>{RepeatAlerts.byId[id].description}</p>
                    </TableCell>
                    <TableCell align="center">
                      <Grid container>
                        <Grid item>
                          <FormControlLabel
                            control={(
                              <Checkbox
                                checked={RepeatAlerts.byId[id].warning.enabled}
                                onClick={() => {
                                  updateRepeatAlertDetails(
                                    {
                                      id,
                                      parentId: currentChain,
                                      alert: {
                                        name: RepeatAlerts.byId[id].name,
                                        identifier: RepeatAlerts.byId[id].identifier,
                                        description: RepeatAlerts.byId[id].description,
                                        adornment: RepeatAlerts.byId[id].adornment,
                                        warning: {
                                          delay: RepeatAlerts.byId[id].warning.delay,
                                          repeat: RepeatAlerts.byId[id].warning.repeat,
                                          enabled: !RepeatAlerts.byId[id].warning.enabled,
                                        },
                                        critical: RepeatAlerts.byId[id].critical,
                                        enabled: RepeatAlerts.byId[id].enabled,
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
                              value={RepeatAlerts.byId[id].warning.repeat}
                              type="text"
                              name="repeatWarning"
                              label="Repeat"
                              placeholder="60"
                              onChange={(event) => {
                                updateRepeatAlertDetails({
                                  id,
                                  parentId: currentChain,
                                  alert: {
                                    name: RepeatAlerts.byId[id].name,
                                    identifier: RepeatAlerts.byId[id].identifier,
                                    description: RepeatAlerts.byId[id].description,
                                    adornment: RepeatAlerts.byId[id].adornment,
                                    warning: {
                                      delay: RepeatAlerts.byId[id].warning.delay,
                                      repeat: event.target.value,
                                      enabled: RepeatAlerts.byId[id].warning.enabled,
                                    },
                                    critical: RepeatAlerts.byId[id].critical,
                                    enabled: RepeatAlerts.byId[id].enabled,
                                  },
                                });
                              }}
                              inputProps={{min: 0, style: { textAlign: 'right' }}}
                              InputProps={{
                                endAdornment:
                                  <InputAdornment position="end">
                                    {RepeatAlerts.byId[id].adornment}
                                  </InputAdornment>,
                              }}
                              fullWidth
                            />
                          </Grid>
                        </Grid>
                      </Grid>
                    </TableCell>
                    <TableCell align="center">
                      <Grid container>
                        <Grid item>
                          <FormControlLabel
                            control={(
                              <Checkbox
                                checked={RepeatAlerts.byId[id].critical.enabled}
                                onClick={() => {
                                  updateRepeatAlertDetails(
                                    {
                                      id,
                                      parentId: currentChain,
                                      alert: {
                                        name: RepeatAlerts.byId[id].name,
                                        identifier: RepeatAlerts.byId[id].identifier,
                                        description: RepeatAlerts.byId[id].description,
                                        adornment: RepeatAlerts.byId[id].adornment,
                                        warning: RepeatAlerts.byId[id].warning,
                                        critical: {
                                          delay: RepeatAlerts.byId[id].critical.delay,
                                          repeat: RepeatAlerts.byId[id].critical.repeat,
                                          enabled: !RepeatAlerts.byId[id].critical.enabled,
                                        },
                                        enabled: RepeatAlerts.byId[id].enabled,
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
                              value={RepeatAlerts.byId[id].critical.repeat}
                              type="text"
                              name="repeatWarning"
                              label="Repeat"
                              placeholder="60"
                              onChange={(event) => {
                                updateRepeatAlertDetails({
                                  id,
                                  parentId: currentChain,
                                  alert: {
                                    name: RepeatAlerts.byId[id].name,
                                    identifier: RepeatAlerts.byId[id].identifier,
                                    description: RepeatAlerts.byId[id].description,
                                    adornment: RepeatAlerts.byId[id].adornment,
                                    warning: {
                                      delay: RepeatAlerts.byId[id].critical.delay,
                                      repeat: event.target.value,
                                      enabled: RepeatAlerts.byId[id].critical.enabled,
                                    },
                                    critical: RepeatAlerts.byId[id].critical,
                                    enabled: RepeatAlerts.byId[id].enabled,
                                  },
                                });
                              }}
                              inputProps={{min: 0, style: { textAlign: 'right' }}}
                              InputProps={{
                                endAdornment:
                                  <InputAdornment position="end">
                                    {RepeatAlerts.byId[id].adornment}
                                  </InputAdornment>,
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
                            checked={RepeatAlerts.byId[id].enabled}
                            onClick={() => {
                              updateRepeatAlertDetails({
                                id,
                                parentId: currentChain,
                                alert: {
                                  name: RepeatAlerts.byId[id].name,
                                  identifier: RepeatAlerts.byId[id].identifier,
                                  description: RepeatAlerts.byId[id].description,
                                  adornment: RepeatAlerts.byId[id].adornment,
                                  warning: RepeatAlerts.byId[id].warning,
                                  critical: RepeatAlerts.byId[id].critical,
                                  enabled: !RepeatAlerts.byId[id].enabled,
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
                {TimeWindowAlerts.allIds.map((id) => (
                  <TableRow key={id}>
                    <TableCell align="center">
                      <h4><b>{TimeWindowAlerts.byId[id].name}</b></h4>
                      <p>{TimeWindowAlerts.byId[id].description}</p>
                    </TableCell>
                    <TableCell align="center">
                      <Grid container>
                        <Grid item>
                          <FormControlLabel
                            control={(
                              <Checkbox
                                checked={TimeWindowAlerts.byId[id].warning.enabled}
                                onClick={() => {
                                  updateTimeWindowAlertDetails(
                                    {
                                      id,
                                      parentId: currentChain,
                                      alert: {
                                        name: TimeWindowAlerts.byId[id].name,
                                        identifier: TimeWindowAlerts.byId[id].identifier,
                                        description: TimeWindowAlerts.byId[id].description,
                                        adornment_threshold: TimeWindowAlerts.byId[id].adornment_threshold,
                                        adornment_time: TimeWindowAlerts.byId[id].adornment_time,
                                        warning: {
                                          threshold: TimeWindowAlerts.byId[id].warning.threshold,
                                          time_window: TimeWindowAlerts.byId[id].warning.time_window,
                                          enabled: !TimeWindowAlerts.byId[id].warning.enabled,
                                        },
                                        critical: TimeWindowAlerts.byId[id].critical,
                                        enabled: TimeWindowAlerts.byId[id].enabled,
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
                              value={TimeWindowAlerts.byId[id].warning.threshold}
                              type="text"
                              name="thresholdWarning"
                              label="Threshold"
                              placeholder="60"
                              onChange={(event) => {
                                updateTimeWindowAlertDetails(
                                  {
                                    id,
                                    parentId: currentChain,
                                    alert: {
                                      name: TimeWindowAlerts.byId[id].name,
                                      identifier: TimeWindowAlerts.byId[id].identifier,
                                      description: TimeWindowAlerts.byId[id].description,
                                      adornment_threshold: TimeWindowAlerts.byId[id].adornment_threshold,
                                      adornment_time: TimeWindowAlerts.byId[id].adornment_time,
                                      warning: {
                                        threshold: event.target.value,
                                        time_window: TimeWindowAlerts.byId[id].warning.time_window,
                                        enabled: TimeWindowAlerts.byId[id].warning.enabled,
                                      },
                                      critical: TimeWindowAlerts.byId[id].critical,
                                      enabled: TimeWindowAlerts.byId[id].enabled,
                                    },
                                  },
                                );
                              }}
                              inputProps={{min: 0, style: { textAlign: 'right' }}}
                              InputProps={{
                                endAdornment:
                                  <InputAdornment position="end">
                                    {TimeWindowAlerts.byId[id].adornment_threshold}
                                  </InputAdornment>,
                              }}
                              fullWidth
                            />
                          </Grid>
                          <Grid container>
                            <TextField
                              value={TimeWindowAlerts.byId[id].warning.time_window}
                              type="text"
                              name="timewindowWarning"
                              label="Repeat"
                              placeholder="60"
                              onChange={(event) => {
                                updateTimeWindowAlertDetails({
                                  id,
                                  parentId: currentChain,
                                  alert: {
                                    name: TimeWindowAlerts.byId[id].name,
                                    identifier: TimeWindowAlerts.byId[id].identifier,
                                    description: TimeWindowAlerts.byId[id].description,
                                    adornment_threshold: TimeWindowAlerts.byId[id].adornment_threshold,
                                    adornment_time: TimeWindowAlerts.byId[id].adornment_time,
                                    warning: {
                                      threshold: TimeWindowAlerts.byId[id].warning.threshold,
                                      time_window: event.target.value,
                                      enabled: TimeWindowAlerts.byId[id].warning.enabled,
                                    },
                                    critical: TimeWindowAlerts.byId[id].critical,
                                    enabled: TimeWindowAlerts.byId[id].enabled,
                                  },
                                });
                              }}
                              inputProps={{min: 0, style: { textAlign: 'right' }}}
                              InputProps={{
                                endAdornment:
                                  <InputAdornment position="end">
                                    {TimeWindowAlerts.byId[id].adornment_time}
                                  </InputAdornment>,
                              }}
                              fullWidth
                            />
                          </Grid>
                        </Grid>
                      </Grid>
                    </TableCell>
                    <TableCell align="center">
                      <Grid container>
                        <Grid item>
                          <FormControlLabel
                            control={(
                              <Checkbox
                                checked={TimeWindowAlerts.byId[id].critical.enabled}
                                onClick={() => {
                                  updateTimeWindowAlertDetails(
                                    {
                                      id,
                                      parentId: currentChain,
                                      alert: {
                                        name: TimeWindowAlerts.byId[id].name,
                                        identifier: TimeWindowAlerts.byId[id].identifier,
                                        description: TimeWindowAlerts.byId[id].description,
                                        adornment_threshold: TimeWindowAlerts.byId[id].adornment_threshold,
                                        adornment_time: TimeWindowAlerts.byId[id].adornment_time,
                                        warning: TimeWindowAlerts.byId[id].warning,
                                        critical: {
                                          threshold: TimeWindowAlerts.byId[id].critical.threshold,
                                          time_window: TimeWindowAlerts.byId[id].critical.time_window,
                                          enabled: !TimeWindowAlerts.byId[id].critical.enabled,
                                        },
                                        enabled: TimeWindowAlerts.byId[id].enabled,
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
                            value={TimeWindowAlerts.byId[id].critical.threshold}
                            type="text"
                            name="thresholdWarning"
                            label="Threshold"
                            placeholder="60"
                            onChange={(event) => {
                              updateTimeWindowAlertDetails(
                                {
                                  id,
                                  parentId: currentChain,
                                  alert: {
                                    name: TimeWindowAlerts.byId[id].name,
                                    identifier: TimeWindowAlerts.byId[id].identifier,
                                    description: TimeWindowAlerts.byId[id].description,
                                    adornment_threshold: TimeWindowAlerts.byId[id].adornment_threshold,
                                    adornment_time: TimeWindowAlerts.byId[id].adornment_time,
                                    warning: TimeWindowAlerts.byId[id].warning,
                                    critical: {
                                      threshold: event.target.value,
                                      time_window: TimeWindowAlerts.byId[id].critical.time_window,
                                      enabled: TimeWindowAlerts.byId[id].critical.enabled,
                                    },
                                    enabled: TimeWindowAlerts.byId[id].enabled,
                                  },
                                },
                              );
                            }}
                            inputProps={{min: 0, style: { textAlign: 'right' }}}
                            InputProps={{
                              endAdornment:
                                <InputAdornment position="end">
                                  {TimeWindowAlerts.byId[id].adornment_threshold}
                                </InputAdornment>,
                            }}
                            fullWidth
                          />
                        </Grid>
                        <Grid container>
                          <TextField
                            value={TimeWindowAlerts.byId[id].critical.time_window}
                            type="text"
                            name="timewindowWarning"
                            label="Repeat"
                            placeholder="60"
                            onChange={(event) => {
                              updateTimeWindowAlertDetails({
                                id,
                                parentId: currentChain,
                                alert: {
                                  name: TimeWindowAlerts.byId[id].name,
                                  identifier: TimeWindowAlerts.byId[id].identifier,
                                  description: TimeWindowAlerts.byId[id].description,
                                  adornment_threshold: TimeWindowAlerts.byId[id].adornment_threshold,
                                  adornment_time: TimeWindowAlerts.byId[id].adornment_time,
                                  warning: TimeWindowAlerts.byId[id].warning,
                                  critical: {
                                    threshold: TimeWindowAlerts.byId[id].critical.threshold,
                                    time_window: event.target.value,
                                    enabled: TimeWindowAlerts.byId[id].critical.enabled,
                                  },
                                  enabled: TimeWindowAlerts.byId[id].enabled,
                                },
                              });
                            }}
                            inputProps={{min: 0, style: { textAlign: 'right' }}}
                            InputProps={{
                              endAdornment:
                                <InputAdornment position="end">
                                  {TimeWindowAlerts.byId[id].adornment_time}
                                </InputAdornment>,
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
                            checked={TimeWindowAlerts.byId[id].enabled}
                            onClick={() => {
                              updateTimeWindowAlertDetails({
                                id,
                                parentId: currentChain,
                                alert: {
                                  name: TimeWindowAlerts.byId[id].name,
                                  identifier: TimeWindowAlerts.byId[id].identifier,
                                  description: TimeWindowAlerts.byId[id].description,
                                  adornment_threshold: TimeWindowAlerts.byId[id].adornment_threshold,
                                  adornment_time: TimeWindowAlerts.byId[id].adornment_time,
                                  warning: TimeWindowAlerts.byId[id].warning,
                                  critical: TimeWindowAlerts.byId[id].critical,
                                  enabled: !TimeWindowAlerts.byId[id].enabled,
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
                {ThresholdAlerts.allIds.map((id) => (
                  <TableRow key={id}>
                    <TableCell align="center">
                      <h4><b>{ThresholdAlerts.byId[id].name}</b></h4>
                      <p>{ThresholdAlerts.byId[id].description}</p>
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
                                        identifier: ThresholdAlerts.byId[id].identifier,
                                        description: ThresholdAlerts.byId[id].description,
                                        adornment: ThresholdAlerts.byId[id].adornment,
                                        adornment_time: ThresholdAlerts.byId[id].adornment_time,
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
                                      identifier: ThresholdAlerts.byId[id].identifier,
                                      description: ThresholdAlerts.byId[id].description,
                                      adornment: ThresholdAlerts.byId[id].adornment,
                                      adornment_time: ThresholdAlerts.byId[id].adornment_time,
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
                              inputProps={{min: 0, style: { textAlign: 'right' }}}
                              InputProps={{
                                endAdornment:
                                  <InputAdornment position="end">
                                    {ThresholdAlerts.byId[id].adornment}
                                  </InputAdornment>,
                              }}
                              fullWidth
                            />
                          </Grid>
                        </Grid>
                      </Grid>
                    </TableCell>
                    <TableCell align="center">
                      <Grid container>
                        <Grid item>
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
                                        identifier: ThresholdAlerts.byId[id].identifier,
                                        description: ThresholdAlerts.byId[id].description,
                                        adornment: ThresholdAlerts.byId[id].adornment,
                                        adornment_time: ThresholdAlerts.byId[id].adornment_time,
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
                        </Grid>
                        <Grid item>
                          <Grid container>
                            <TextField
                              value={ThresholdAlerts.byId[id].critical.threshold}
                              type="text"
                              name="thresholdCritical"
                              label="Threshold"
                              placeholder="60"
                              onChange={(event) => {
                                updateThresholdAlertDetails(
                                  {
                                    id,
                                    parentId: currentChain,
                                    alert: {
                                      name: ThresholdAlerts.byId[id].name,
                                      identifier: ThresholdAlerts.byId[id].identifier,
                                      description: ThresholdAlerts.byId[id].description,
                                      adornment: ThresholdAlerts.byId[id].adornment,
                                      adornment_time: ThresholdAlerts.byId[id].adornment_time,
                                      warning: ThresholdAlerts.byId[id].warning,
                                      critical: {
                                        threshold: event.target.value,
                                        repeat: ThresholdAlerts.byId[id].critical.repeat,
                                        enabled: ThresholdAlerts.byId[id].critical.enabled,
                                      },
                                      enabled: ThresholdAlerts.byId[id].enabled,
                                    },
                                  },
                                );
                              }}
                              inputProps={{min: 0, style: { textAlign: 'right' }}}
                              InputProps={{
                                endAdornment:
                                  <InputAdornment position="end">
                                    {ThresholdAlerts.byId[id].adornment}
                                  </InputAdornment>,
                              }}
                              fullWidth
                            />
                          </Grid>
                          <Grid container>
                            <TextField
                              value={ThresholdAlerts.byId[id].critical.repeat}
                              type="text"
                              name="thresholdCritical"
                              label="Repeat"
                              placeholder="60"
                              onChange={(event) => {
                                updateThresholdAlertDetails(
                                  {
                                    id,
                                    parentId: currentChain,
                                    alert: {
                                      name: ThresholdAlerts.byId[id].name,
                                      identifier: ThresholdAlerts.byId[id].identifier,
                                      description: ThresholdAlerts.byId[id].description,
                                      adornment: ThresholdAlerts.byId[id].adornment,
                                      adornment_time: ThresholdAlerts.byId[id].adornment_time,
                                      warning: ThresholdAlerts.byId[id].warning,
                                      critical: {
                                        threshold: ThresholdAlerts.byId[id].critical.threshold,
                                        repeat: event.target.value,
                                        enabled: ThresholdAlerts.byId[id].critical.enabled,
                                      },
                                      enabled: ThresholdAlerts.byId[id].enabled,
                                    },
                                  },
                                );
                              }}
                              inputProps={{min: 0, style: { textAlign: 'right' }}}
                              InputProps={{
                                endAdornment:
                                  <InputAdornment position="end">
                                    {ThresholdAlerts.byId[id].adornment_time}
                                  </InputAdornment>,
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
                            checked={ThresholdAlerts.byId[id].enabled}
                            onClick={() => {
                              updateThresholdAlertDetails({
                                id,
                                parentId: currentChain,
                                alert: {
                                  name: ThresholdAlerts.byId[id].name,
                                  identifier: ThresholdAlerts.byId[id].identifier,
                                  description: ThresholdAlerts.byId[id].description,
                                  adornment: ThresholdAlerts.byId[id].adornment,
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
        <div className={classes.subsection}>
          <GridContainer justify="center">
            <GridItem xs={12} sm={12} md={8}>
              <h1 className={classes.title}>
                {Data.subtitle_2}
              </h1>
            </GridItem>
          </GridContainer>
        </div>
        <Box py={4}>
          <TableContainer component={Paper}>
            <Table aria-label="simple table">
              <TableHead>
                <TableRow>
                  <TableCell align="center">Alert</TableCell>
                  <TableCell align="center">Severity</TableCell>
                  <TableCell align="center">Enabled</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {SeverityAlerts.allIds.map((id) => (
                  <TableRow key={id}>
                    <TableCell align="center">
                      <h4><b>{SeverityAlerts.byId[id].name}</b></h4>
                      <p>{SeverityAlerts.byId[id].description}</p>
                    </TableCell>
                    <TableCell align="center">
                      <FormControl>
                        <Select
                          labelId="severity"
                          id="severity-selection"
                          value={SeverityAlerts.byId[id].severity}
                          onChange={(event) => {
                            updateSeverityAlertDetails(
                              {
                                id,
                                parentId: currentChain,
                                alert: {
                                  name: SeverityAlerts.byId[id].name,
                                  identifier: ThresholdAlerts.byId[id].identifier,
                                  description: SeverityAlerts.byId[id].description,
                                  severity: event.target.value,
                                  enabled: SeverityAlerts.byId[id].enabled,
                                },
                              },
                            );
                          }}
                        >
                          <MenuItem value="INFO">Info</MenuItem>
                          <MenuItem value="WARNING">Warning</MenuItem>
                          <MenuItem value="CRITICAL">Critical</MenuItem>
                        </Select>
                      </FormControl>
                    </TableCell>
                    <TableCell align="center">
                      <FormControlLabel
                        control={(
                          <Checkbox
                            checked={SeverityAlerts.byId[id].enabled}
                            onClick={() => {
                              updateSeverityAlertDetails(
                                {
                                  id,
                                  parentId: currentChain,
                                  alert: {
                                    name: SeverityAlerts.byId[id].name,
                                    identifier: ThresholdAlerts.byId[id].identifier,
                                    description: SeverityAlerts.byId[id].description,
                                    severity: SeverityAlerts.byId[id].severity,
                                    enabled: !SeverityAlerts.byId[id].enabled,
                                  },
                                },
                              );
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
    </MuiThemeProvider>
  );
};

AlertsTable.propTypes = forbidExtraProps({
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
        allIds: [],
      }),
      timeWindowAlerts: PropTypes.shape({
        byId: PropTypes.shape({
          name: PropTypes.string,
          description: PropTypes.string,
          warning: PropTypes.shape({
            threshold: PropTypes.number,
            time_window: PropTypes.number,
            enabled: PropTypes.bool,
          }),
          critical: PropTypes.shape({
            threshold: PropTypes.number,
            time_window: PropTypes.number,
            enabled: PropTypes.bool,
          }),
          enabled: PropTypes.bool,
        }),
        allIds: [],
      }),
      thresholdAlerts: PropTypes.shape({
        byId: PropTypes.shape({
          name: PropTypes.string,
          description: PropTypes.string,
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
      severityAlerts: PropTypes.shape({
        byId: PropTypes.shape({
          name: PropTypes.string,
          description: PropTypes.string,
          severity: PropTypes.string,
          enabled: PropTypes.bool,
        }),
        allIds: [],
      }),
    }).isRequired,
    allIds: [],
  }).isRequired,
  currentChain: PropTypes.string.isRequired,
  clearChainId: PropTypes.func.isRequired,
  updateRepeatAlertDetails: PropTypes.func.isRequired,
  updateTimeWindowAlertDetails: PropTypes.func.isRequired,
  updateThresholdAlertDetails: PropTypes.func.isRequired,
  updateSeverityAlertDetails: PropTypes.func.isRequired,
});

export default AlertsTable;
