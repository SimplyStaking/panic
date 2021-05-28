import React from 'react';
import PropTypes from 'prop-types';
import {
  Table, TableBody, TableContainer, TableHead, TableRow, FormControlLabel,
  Checkbox, Typography, Grid, Box, MenuItem, Select, FormControl,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import StepButtonContainer from 'containers/chains/common/stepButtonContainer';
import NavigationButton from 'components/global/navigationButton';
import {
  CHAINS_PAGE,
  DONE,
  BACK,
  CHANNELS_STEP,
  CHAINS_STEP,
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
 * AlertsTable will show display all the 4 alert types together with the
 * functions to directly edit them.
 */
const AlertsTable = ({
  config,
  currentChain,
  updateRepeatAlertDetails,
  updateTimeWindowAlertDetails,
  updateThresholdAlertDetails,
  updateSeverityAlertDetails,
  pageChanger,
  stepChanger,
  clearChainId,
}) => {
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
              <h1 className={classes.title}>{Data.title}</h1>
            </GridItem>
          </GridContainer>
        </div>
        <Typography variant="subtitle1" gutterBottom className="greyBackground">
          <Box m={2} p={3}>
            <p
              style={{
                fontWeight: '350',
                fontSize: '1.2rem',
              }}
            >
              {Data.description}
            </p>
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
            <Table aria-label="alert-table-1" style={{ tableLayout: 'fixed' }}>
              <TableHead>
                <TableRow>
                  <StyledTableCell align="center">Alert</StyledTableCell>
                  <StyledTableCell align="center">Warning Threshold</StyledTableCell>
                  <StyledTableCell align="center">Critical Threshold</StyledTableCell>
                  <StyledTableCell align="center">Enabled</StyledTableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {RepeatAlerts.allIds.map((id) => (
                  <StyledTableRow key={id}>
                    <StyledTableCell align="left">
                      <h4>
                        <b>{RepeatAlerts.byId[id].name}</b>
                      </h4>
                      <p>{RepeatAlerts.byId[id].description}</p>
                    </StyledTableCell>
                    <StyledTableCell align="center">
                      <Grid container spacing={1} justify="flex-end" alignItems="flex-end">
                        <Grid item>
                          <FormControlLabel
                            control={(
                              <Checkbox
                                checked={RepeatAlerts.byId[id].warning.enabled}
                                onClick={() => {
                                  updateRepeatAlertDetails({
                                    id,
                                    parent_id: currentChain,
                                    alert: {
                                      name: RepeatAlerts.byId[id].name,
                                      identifier:
                                        RepeatAlerts.byId[id].identifier,
                                      description:
                                        RepeatAlerts.byId[id].description,
                                      adornment:
                                        RepeatAlerts.byId[id].adornment,
                                      warning: {
                                        repeat:
                                          RepeatAlerts.byId[id].warning.repeat,
                                        enabled: !RepeatAlerts.byId[id].warning
                                          .enabled,
                                      },
                                      critical: RepeatAlerts.byId[id].critical,
                                      enabled: RepeatAlerts.byId[id].enabled,
                                    },
                                  });
                                }}
                                color="primary"
                              />
                            )}
                            label="Enabled"
                            labelPlacement="start"
                          />
                        </Grid>
                        <Grid item>
                          <CssTextField
                            id={('repeat-warning-outlined-full-width-'.concat(id))}
                            value={RepeatAlerts.byId[id].warning.repeat}
                            label="Repeat"
                            type="text"
                            style={{ margin: 8 }}
                            name="repeatWarning"
                            placeholder="60"
                            onChange={(event) => {
                              updateRepeatAlertDetails({
                                id,
                                parent_id: currentChain,
                                alert: {
                                  name: RepeatAlerts.byId[id].name,
                                  identifier:
                                    RepeatAlerts.byId[id].identifier,
                                  description:
                                    RepeatAlerts.byId[id].description,
                                  adornment: RepeatAlerts.byId[id].adornment,
                                  warning: {
                                    repeat: event.target.value,
                                    enabled:
                                      RepeatAlerts.byId[id].warning.enabled,
                                  },
                                  critical: RepeatAlerts.byId[id].critical,
                                  enabled: RepeatAlerts.byId[id].enabled,
                                },
                              });
                            }}
                            fullWidth
                            margin="normal"
                            InputLabelProps={{
                              shrink: true,
                            }}
                            variant="outlined"
                            autoComplete="off"
                            InputProps={{
                              endAdornment: (
                                <InputAdornment position="end">
                                  {RepeatAlerts.byId[id].adornment}
                                </InputAdornment>
                              ),
                              min: 0,
                              style: { textAlign: 'right' },
                            }}
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
                                checked={RepeatAlerts.byId[id].critical.enabled}
                                onClick={() => {
                                  updateRepeatAlertDetails({
                                    id,
                                    parent_id: currentChain,
                                    alert: {
                                      name: RepeatAlerts.byId[id].name,
                                      identifier:
                                        RepeatAlerts.byId[id].identifier,
                                      description:
                                        RepeatAlerts.byId[id].description,
                                      adornment:
                                        RepeatAlerts.byId[id].adornment,
                                      warning: RepeatAlerts.byId[id].warning,
                                      critical: {
                                        repeat:
                                          RepeatAlerts.byId[id].critical.repeat,
                                        enabled: !RepeatAlerts.byId[id].critical
                                          .enabled,
                                      },
                                      enabled: RepeatAlerts.byId[id].enabled,
                                    },
                                  });
                                }}
                                color="primary"
                              />
                            )}
                            label="Enabled"
                            labelPlacement="start"
                          />
                        </Grid>
                        <Grid item>
                          <CssTextField
                            id={('repeat-critical-outlined-full-width-'.concat(id))}
                            value={RepeatAlerts.byId[id].critical.repeat}
                            label="Repeat"
                            type="text"
                            style={{ margin: 8 }}
                            name="repeatCritical"
                            placeholder="60"
                            onChange={(event) => {
                              updateRepeatAlertDetails({
                                id,
                                parent_id: currentChain,
                                alert: {
                                  name: RepeatAlerts.byId[id].name,
                                  identifier:
                                    RepeatAlerts.byId[id].identifier,
                                  description:
                                    RepeatAlerts.byId[id].description,
                                  adornment: RepeatAlerts.byId[id].adornment,
                                  warning: RepeatAlerts.byId[id].warning,
                                  critical: {
                                    repeat: event.target.value,
                                    enabled:
                                      RepeatAlerts.byId[id].critical.enabled,
                                  },
                                  enabled: RepeatAlerts.byId[id].enabled,
                                },
                              });
                            }}
                            fullWidth
                            margin="normal"
                            InputLabelProps={{
                              shrink: true,
                            }}
                            variant="outlined"
                            autoComplete="off"
                            InputProps={{
                              endAdornment: (
                                <InputAdornment position="end">
                                  {RepeatAlerts.byId[id].adornment}
                                </InputAdornment>
                              ),
                              min: 0,
                              style: { textAlign: 'right' },
                            }}
                          />
                        </Grid>
                      </Grid>
                    </StyledTableCell>
                    <StyledTableCell align="center">
                      <FormControlLabel
                        control={(
                          <Checkbox
                            checked={RepeatAlerts.byId[id].enabled}
                            onClick={() => {
                              updateRepeatAlertDetails({
                                id,
                                parent_id: currentChain,
                                alert: {
                                  name: RepeatAlerts.byId[id].name,
                                  identifier: RepeatAlerts.byId[id].identifier,
                                  description:
                                    RepeatAlerts.byId[id].description,
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
                        label=""
                      />
                    </StyledTableCell>
                  </StyledTableRow>
                ))}
                {TimeWindowAlerts.allIds.map((id) => (
                  <StyledTableRow key={id}>
                    <StyledTableCell align="left">
                      <h4>
                        <b>{TimeWindowAlerts.byId[id].name}</b>
                      </h4>
                      <p>{TimeWindowAlerts.byId[id].description}</p>
                    </StyledTableCell>
                    <StyledTableCell align="center">
                      <Grid container spacing={1} justify="flex-end" alignItems="center">
                        <Grid item>
                          <FormControlLabel
                            control={(
                              <Checkbox
                                checked={
                                  TimeWindowAlerts.byId[id].warning.enabled
                                }
                                onClick={() => {
                                  updateTimeWindowAlertDetails({
                                    id,
                                    parent_id: currentChain,
                                    alert: {
                                      name: TimeWindowAlerts.byId[id].name,
                                      identifier:
                                        TimeWindowAlerts.byId[id].identifier,
                                      description:
                                        TimeWindowAlerts.byId[id].description,
                                      adornment_threshold:
                                        TimeWindowAlerts.byId[id]
                                          .adornment_threshold,
                                      adornment_time:
                                        TimeWindowAlerts.byId[id]
                                          .adornment_time,
                                      warning: {
                                        threshold:
                                          TimeWindowAlerts.byId[id].warning
                                            .threshold,
                                        time_window:
                                          TimeWindowAlerts.byId[id].warning
                                            .time_window,
                                        enabled: !TimeWindowAlerts.byId[id]
                                          .warning.enabled,
                                      },
                                      critical:
                                        TimeWindowAlerts.byId[id].critical,
                                      enabled:
                                        TimeWindowAlerts.byId[id].enabled,
                                    },
                                  });
                                }}
                                color="primary"
                              />
                            )}
                            label="Enabled"
                            labelPlacement="start"
                          />
                        </Grid>
                        <Grid item>
                          <CssTextField
                            id={('time-window-warning-threshold-outlined-full-width-'.concat(id))}
                            value={
                              TimeWindowAlerts.byId[id].warning.threshold
                            }
                            label="Threshold"
                            type="text"
                            style={{ margin: 8 }}
                            name="thresholdWarning"
                            placeholder="60"
                            onChange={(event) => {
                              updateTimeWindowAlertDetails({
                                id,
                                parent_id: currentChain,
                                alert: {
                                  name: TimeWindowAlerts.byId[id].name,
                                  identifier:
                                    TimeWindowAlerts.byId[id].identifier,
                                  description:
                                    TimeWindowAlerts.byId[id].description,
                                  adornment_threshold:
                                    TimeWindowAlerts.byId[id]
                                      .adornment_threshold,
                                  adornment_time:
                                    TimeWindowAlerts.byId[id].adornment_time,
                                  warning: {
                                    threshold: event.target.value,
                                    time_window:
                                      TimeWindowAlerts.byId[id].warning
                                        .time_window,
                                    enabled:
                                      TimeWindowAlerts.byId[id].warning
                                        .enabled,
                                  },
                                  critical:
                                    TimeWindowAlerts.byId[id].critical,
                                  enabled: TimeWindowAlerts.byId[id].enabled,
                                },
                              });
                            }}
                            fullWidth
                            margin="normal"
                            InputLabelProps={{
                              shrink: true,
                            }}
                            variant="outlined"
                            autoComplete="off"
                            InputProps={{
                              endAdornment: (
                                <InputAdornment position="end">
                                  {TimeWindowAlerts.byId[id].adornment_threshold}
                                </InputAdornment>
                              ),
                              min: 0,
                              style: { textAlign: 'right' },
                            }}
                          />
                        </Grid>
                        <Grid item>
                          <CssTextField
                            id={('time-window-warning-time-window-outlined-full-width-'.concat(id))}
                            value={
                              TimeWindowAlerts.byId[id].warning.time_window
                            }
                            label="Time Window"
                            type="text"
                            style={{ margin: 8 }}
                            name="timeWindowWarning"
                            placeholder="60"
                            onChange={(event) => {
                              updateTimeWindowAlertDetails({
                                id,
                                parent_id: currentChain,
                                alert: {
                                  name: TimeWindowAlerts.byId[id].name,
                                  identifier:
                                    TimeWindowAlerts.byId[id].identifier,
                                  description:
                                    TimeWindowAlerts.byId[id].description,
                                  adornment_threshold:
                                    TimeWindowAlerts.byId[id]
                                      .adornment_threshold,
                                  adornment_time:
                                    TimeWindowAlerts.byId[id].adornment_time,
                                  warning: {
                                    threshold:
                                      TimeWindowAlerts.byId[id].warning
                                        .threshold,
                                    time_window: event.target.value,
                                    enabled:
                                      TimeWindowAlerts.byId[id].warning
                                        .enabled,
                                  },
                                  critical:
                                    TimeWindowAlerts.byId[id].critical,
                                  enabled: TimeWindowAlerts.byId[id].enabled,
                                },
                              });
                            }}
                            fullWidth
                            margin="normal"
                            InputLabelProps={{
                              shrink: true,
                            }}
                            variant="outlined"
                            autoComplete="off"
                            InputProps={{
                              endAdornment: (
                                <InputAdornment position="end">
                                  {TimeWindowAlerts.byId[id].adornment_time}
                                </InputAdornment>
                              ),
                              min: 0,
                              style: { textAlign: 'right' },
                            }}
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
                                  TimeWindowAlerts.byId[id].critical.enabled
                                }
                                onClick={() => {
                                  updateTimeWindowAlertDetails({
                                    id,
                                    parent_id: currentChain,
                                    alert: {
                                      name: TimeWindowAlerts.byId[id].name,
                                      identifier:
                                        TimeWindowAlerts.byId[id].identifier,
                                      description:
                                        TimeWindowAlerts.byId[id].description,
                                      adornment_threshold:
                                        TimeWindowAlerts.byId[id]
                                          .adornment_threshold,
                                      adornment_time:
                                        TimeWindowAlerts.byId[id]
                                          .adornment_time,
                                      warning:
                                        TimeWindowAlerts.byId[id].warning,
                                      critical: {
                                        threshold:
                                          TimeWindowAlerts.byId[id].critical
                                            .threshold,
                                        time_window:
                                          TimeWindowAlerts.byId[id].critical
                                            .time_window,
                                        enabled: !TimeWindowAlerts.byId[id]
                                          .critical.enabled,
                                      },
                                      enabled:
                                        TimeWindowAlerts.byId[id].enabled,
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
                            id={('time-window-critical-threshold-outlined-full-width-'.concat(id))}
                            value={
                              TimeWindowAlerts.byId[id].critical.threshold
                            }
                            label="Threshold"
                            type="text"
                            style={{ margin: 8 }}
                            name="thresholdCritical"
                            placeholder="60"
                            onChange={(event) => {
                              updateTimeWindowAlertDetails({
                                id,
                                parent_id: currentChain,
                                alert: {
                                  name: TimeWindowAlerts.byId[id].name,
                                  identifier:
                                    TimeWindowAlerts.byId[id].identifier,
                                  description:
                                    TimeWindowAlerts.byId[id].description,
                                  adornment_threshold:
                                    TimeWindowAlerts.byId[id]
                                      .adornment_threshold,
                                  adornment_time:
                                    TimeWindowAlerts.byId[id].adornment_time,
                                  warning: TimeWindowAlerts.byId[id].warning,
                                  critical: {
                                    threshold: event.target.value,
                                    time_window:
                                      TimeWindowAlerts.byId[id].critical
                                        .time_window,
                                    repeat:
                                      TimeWindowAlerts.byId[id].critical
                                        .repeat,
                                    enabled:
                                      TimeWindowAlerts.byId[id].critical
                                        .enabled,
                                  },
                                  enabled: TimeWindowAlerts.byId[id].enabled,
                                },
                              });
                            }}
                            fullWidth
                            margin="normal"
                            InputLabelProps={{
                              shrink: true,
                            }}
                            variant="outlined"
                            autoComplete="off"
                            InputProps={{
                              endAdornment: (
                                <InputAdornment position="end">
                                  {TimeWindowAlerts.byId[id].adornment_threshold}
                                </InputAdornment>
                              ),
                              min: 0,
                              style: { textAlign: 'right' },
                            }}
                          />
                          <Grid item>
                            <CssTextField
                              id={('time-window-critical-time-window-outlined-full-width-'.concat(id))}
                              value={
                                TimeWindowAlerts.byId[id].critical.time_window
                              }
                              label="Time Window"
                              type="text"
                              style={{ margin: 8 }}
                              name="timeWindowCriticalTW"
                              placeholder="60"
                              onChange={(event) => {
                                updateTimeWindowAlertDetails({
                                  id,
                                  parent_id: currentChain,
                                  alert: {
                                    name: TimeWindowAlerts.byId[id].name,
                                    identifier:
                                      TimeWindowAlerts.byId[id].identifier,
                                    description:
                                      TimeWindowAlerts.byId[id].description,
                                    adornment_threshold:
                                      TimeWindowAlerts.byId[id]
                                        .adornment_threshold,
                                    adornment_time:
                                      TimeWindowAlerts.byId[id].adornment_time,
                                    warning: TimeWindowAlerts.byId[id].warning,
                                    critical: {
                                      threshold:
                                        TimeWindowAlerts.byId[id].critical
                                          .threshold,
                                      time_window: event.target.value,
                                      repeat:
                                        TimeWindowAlerts.byId[id].critical
                                          .repeat,
                                      enabled:
                                        TimeWindowAlerts.byId[id].critical
                                          .enabled,
                                    },
                                    enabled: TimeWindowAlerts.byId[id].enabled,
                                  },
                                });
                              }}
                              fullWidth
                              margin="normal"
                              InputLabelProps={{
                                shrink: true,
                              }}
                              variant="outlined"
                              autoComplete="off"
                              InputProps={{
                                endAdornment: (
                                  <InputAdornment position="end">
                                    {TimeWindowAlerts.byId[id].adornment_time}
                                  </InputAdornment>
                                ),
                                min: 0,
                                style: { textAlign: 'right' },
                              }}
                            />
                          </Grid>
                          <Grid item>
                            <CssTextField
                              id={('time-window-critical-repeat-outlined-full-width-'.concat(id))}
                              value={
                                TimeWindowAlerts.byId[id].critical.repeat
                              }
                              label="Repeat"
                              type="text"
                              style={{ margin: 8 }}
                              name="repeatCritical"
                              placeholder="60"
                              onChange={(event) => {
                                updateTimeWindowAlertDetails({
                                  id,
                                  parent_id: currentChain,
                                  alert: {
                                    name: TimeWindowAlerts.byId[id].name,
                                    identifier:
                                      TimeWindowAlerts.byId[id].identifier,
                                    description:
                                      TimeWindowAlerts.byId[id].description,
                                    adornment_threshold:
                                      TimeWindowAlerts.byId[id]
                                        .adornment_threshold,
                                    adornment_time:
                                      TimeWindowAlerts.byId[id].adornment_time,
                                    warning: TimeWindowAlerts.byId[id].warning,
                                    critical: {
                                      threshold:
                                        TimeWindowAlerts.byId[id].critical
                                          .threshold,
                                      time_window:
                                        TimeWindowAlerts.byId[id].critical
                                          .time_window,
                                      repeat: event.target.value,
                                      enabled:
                                        TimeWindowAlerts.byId[id].critical
                                          .enabled,
                                    },
                                    enabled: TimeWindowAlerts.byId[id].enabled,
                                  },
                                });
                              }}
                              fullWidth
                              margin="normal"
                              InputLabelProps={{
                                shrink: true,
                              }}
                              variant="outlined"
                              autoComplete="off"
                              InputProps={{
                                endAdornment: (
                                  <InputAdornment position="end">
                                    {TimeWindowAlerts.byId[id].adornment_time}
                                  </InputAdornment>
                                ),
                                min: 0,
                                style: { textAlign: 'right' },
                              }}
                            />
                          </Grid>
                        </Grid>
                      </Grid>
                    </StyledTableCell>
                    <StyledTableCell align="center">
                      <FormControlLabel
                        control={(
                          <Checkbox
                            checked={TimeWindowAlerts.byId[id].enabled}
                            onClick={() => {
                              updateTimeWindowAlertDetails({
                                id,
                                parent_id: currentChain,
                                alert: {
                                  name: TimeWindowAlerts.byId[id].name,
                                  identifier:
                                    TimeWindowAlerts.byId[id].identifier,
                                  description:
                                    TimeWindowAlerts.byId[id].description,
                                  adornment_threshold:
                                    TimeWindowAlerts.byId[id]
                                      .adornment_threshold,
                                  adornment_time:
                                    TimeWindowAlerts.byId[id].adornment_time,
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
                        label=""
                      />
                    </StyledTableCell>
                  </StyledTableRow>
                ))}
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
                            id={('threshold-warning-threshold-outlined-full-width-'.concat(id))}
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
                            fullWidth
                            margin="normal"
                            InputLabelProps={{
                              shrink: true,
                            }}
                            variant="outlined"
                            autoComplete="off"
                            InputProps={{
                              endAdornment: (
                                <InputAdornment position="end">
                                  {ThresholdAlerts.byId[id].adornment}
                                </InputAdornment>
                              ),
                              min: 0,
                              style: { textAlign: 'right' },
                            }}
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
                            fullWidth
                            margin="normal"
                            InputLabelProps={{
                              shrink: true,
                            }}
                            variant="outlined"
                            autoComplete="off"
                            InputProps={{
                              endAdornment: (
                                <InputAdornment position="end">
                                  {ThresholdAlerts.byId[id].adornment}
                                </InputAdornment>
                              ),
                              min: 0,
                              style: { textAlign: 'right' },
                            }}
                          />
                          <Grid item>
                            <CssTextField
                              id={('threshold-critical-repeat-outlined-full-width-'.concat(id))}
                              value={ThresholdAlerts.byId[id].critical.repeat}
                              label="Repeat"
                              type="text"
                              style={{ margin: 8 }}
                              name="thresholdRepeatCritical"
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
                              fullWidth
                              InputLabelProps={{
                                shrink: true,
                              }}
                              variant="outlined"
                              autoComplete="off"
                              InputProps={{
                                endAdornment: (
                                  <InputAdornment position="end">
                                    {ThresholdAlerts.byId[id].adornment_time}
                                  </InputAdornment>
                                ),
                                min: 0,
                                style: { textAlign: 'right' },
                              }}
                            />
                          </Grid>
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
        {
          SeverityAlerts.allIds.length === 0 ? <div />
            : (
              <div>
                <div className={classes.subsection}>
                  <GridContainer justify="center">
                    <GridItem xs={12} sm={12} md={8}>
                      <h1 className={classes.title}>{Data.subtitle_2}</h1>
                    </GridItem>
                  </GridContainer>
                </div>
                <Box py={4}>
                  <TableContainer component={Paper}>
                    <Table aria-label="severity-alerts-table" style={{ tableLayout: 'fixed' }}>
                      <TableHead>
                        <TableRow>
                          <StyledTableCell align="left">Alert</StyledTableCell>
                          <StyledTableCell align="center">Severity</StyledTableCell>
                          <StyledTableCell align="center">Enabled</StyledTableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {SeverityAlerts.allIds.map((id) => (
                          <StyledTableRow key={id}>
                            <StyledTableCell align="left">
                              <h4>
                                <b>{SeverityAlerts.byId[id].name}</b>
                              </h4>
                              <p>{SeverityAlerts.byId[id].description}</p>
                            </StyledTableCell>
                            <StyledTableCell align="center">
                              <FormControl>
                                <Select
                                  labelId="severity"
                                  id={('severity-selection-'.concat(id))}
                                  value={SeverityAlerts.byId[id].severity}
                                  onChange={(event) => {
                                    updateSeverityAlertDetails({
                                      id,
                                      parent_id: currentChain,
                                      alert: {
                                        name: SeverityAlerts.byId[id].name,
                                        identifier: SeverityAlerts.byId[id].identifier,
                                        description:
                                          SeverityAlerts.byId[id].description,
                                        severity: event.target.value,
                                        enabled: SeverityAlerts.byId[id].enabled,
                                      },
                                    });
                                  }}
                                >
                                  <MenuItem value="INFO">Info</MenuItem>
                                  <MenuItem value="WARNING">Warning</MenuItem>
                                  <MenuItem value="CRITICAL">Critical</MenuItem>
                                </Select>
                              </FormControl>
                            </StyledTableCell>
                            <StyledTableCell align="center">
                              <FormControlLabel
                                control={(
                                  <Checkbox
                                    checked={SeverityAlerts.byId[id].enabled}
                                    onClick={() => {
                                      updateSeverityAlertDetails({
                                        id,
                                        parent_id: currentChain,
                                        alert: {
                                          name: SeverityAlerts.byId[id].name,
                                          identifier:
                                            SeverityAlerts.byId[id].identifier,
                                          description:
                                            SeverityAlerts.byId[id].description,
                                          severity: SeverityAlerts.byId[id].severity,
                                          enabled: !SeverityAlerts.byId[id].enabled,
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
              </div>
            )
        }
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
          identifier: PropTypes.string,
          adornment: PropTypes.string,
          parent_id: PropTypes.string,
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
      timeWindowAlerts: PropTypes.shape({
        byId: PropTypes.shape({
          name: PropTypes.string,
          identifier: PropTypes.string,
          description: PropTypes.string,
          adornment_threshold: PropTypes.string,
          adornment_time: PropTypes.string,
          parent_id: PropTypes.string,
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
        allIds: PropTypes.arrayOf(PropTypes.string),
      }),
      thresholdAlerts: PropTypes.shape({
        byId: PropTypes.shape({
          name: PropTypes.string,
          identifier: PropTypes.string,
          description: PropTypes.string,
          adornment: PropTypes.string,
          adornment_time: PropTypes.string,
          parent_id: PropTypes.string,
          warning: PropTypes.shape({
            threshold: PropTypes.number,
            enabled: PropTypes.bool,
          }),
          critical: PropTypes.shape({
            threshold: PropTypes.number,
            repeat: PropTypes.number,
            enabled: PropTypes.bool,
          }),
          enabled: PropTypes.bool,
        }),
        allIds: PropTypes.arrayOf(PropTypes.string),
      }),
      severityAlerts: PropTypes.shape({
        byId: PropTypes.shape({
          name: PropTypes.string,
          identifier: PropTypes.string,
          description: PropTypes.string,
          parent_id: PropTypes.string,
          severity: PropTypes.string,
          enabled: PropTypes.bool,
        }),
        allIds: PropTypes.arrayOf(PropTypes.string),
      }),
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string),
  }).isRequired,
  currentChain: PropTypes.string.isRequired,
  clearChainId: PropTypes.func.isRequired,
  updateRepeatAlertDetails: PropTypes.func.isRequired,
  updateTimeWindowAlertDetails: PropTypes.func.isRequired,
  updateThresholdAlertDetails: PropTypes.func.isRequired,
  updateSeverityAlertDetails: PropTypes.func.isRequired,
};

export default AlertsTable;
