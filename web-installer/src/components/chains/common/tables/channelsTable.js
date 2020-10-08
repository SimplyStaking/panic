import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import { makeStyles } from '@material-ui/core/styles';
import {
  Grid, FormControlLabel, Checkbox, List, ListItem, Typography, Box,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import { NEXT, BACK } from '../../../../constants/constants';
import StepButtonContainer from
  '../../../../containers/chains/common/stepButtonContainer';

const useStyles = makeStyles({
  table: {
    minWidth: 650,
  },
});

const ChannelsTable = (data, config, currentChain, telegrams, opsgenies,
  emails, pagerduties, twilios, addTelegramDetails, removeTelegramDetails,
  addTwilioDetails, removeTwilioDetails, addEmailDetails, removeEmailDetails,
  addPagerDutyDetails, removePagerDutyDetails, addOpsGenieDetails,
  removeOpsGenieDetails) => {
  const classes = useStyles();

  const currentConfig = config.byId[currentChain];

  return (
    <Grid container className={classes.root} spacing={2}>
      {telegrams.allIds.length !== 0 && (
        <Grid item xs={4}>
          <Grid container justify="center" spacing={3}>
            <Grid item>
              <Paper className={classes.paper}>
                <Typography>
                  Telegram
                </Typography>
                <div
                  style={{ maxHeight: 300, minHeight: 300, overflow: 'auto' }}
                >
                  <List>
                    {telegrams.allIds.map((id) => (
                      <ListItem key={id}>
                        <FormControlLabel
                          control={(
                            <Checkbox
                              checked={currentConfig.telegrams.includes(id)}
                              onClick={() => {
                                const payload = {
                                  id,
                                  parentId: currentChain,
                                };
                                if (currentConfig.telegrams.includes(id)) {
                                  removeTelegramDetails(payload);
                                } else {
                                  addTelegramDetails(payload);
                                }
                              }}
                              name="telegrams"
                              color="primary"
                            />
                          )}
                          label={telegrams.byId[id].botName}
                          labelPlacement="start"
                        />
                      </ListItem>
                    ))}
                  </List>
                </div>
              </Paper>
            </Grid>
          </Grid>
        </Grid>
      )}
      {twilios.allIds.length !== 0 && (
        <Grid item xs={4}>
          <Grid container justify="center" spacing={3}>
            <Grid item>
              <Paper className={classes.paper}>
                <Typography>
                  Twilio
                </Typography>
                <div
                  style={{ maxHeight: 300, minHeight: 300, overflow: 'auto' }}
                >
                  <List>
                    {twilios.allIds.map((id) => (
                      <ListItem key={id}>
                        <FormControlLabel
                          control={(
                            <Checkbox
                              checked={currentConfig.twilios.includes(id)}
                              onClick={() => {
                                const payload = {
                                  id,
                                  parentId: currentChain,
                                };
                                if (currentConfig.twilios.includes(id)) {
                                  removeTwilioDetails(payload);
                                } else {
                                  addTwilioDetails(payload);
                                }
                              }}
                              name="twilios"
                              color="primary"
                            />
                          )}
                          label={twilios.byId[id].configName}
                          labelPlacement="start"
                        />
                      </ListItem>
                    ))}
                  </List>
                </div>
              </Paper>
            </Grid>
          </Grid>
        </Grid>
      )}
      {emails.allIds.length !== 0 && (
        <Grid item xs={4}>
          <Grid container justify="center" spacing={3}>
            <Grid item>
              <Paper className={classes.paper}>
                <Typography>
                  Email
                </Typography>
                <div
                  style={{ maxHeight: 300, minHeight: 300, overflow: 'auto' }}
                >
                  <List>
                    {emails.allIds.map((id) => (
                      <ListItem key={id}>
                        <FormControlLabel
                          control={(
                            <Checkbox
                              checked={currentConfig.emails.includes(id)}
                              onClick={() => {
                                const payload = {
                                  id,
                                  parentId: currentChain,
                                };
                                if (currentConfig.emails.includes(id)) {
                                  removeEmailDetails(payload);
                                } else {
                                  addEmailDetails(payload);
                                }
                              }}
                              name="emails"
                              color="primary"
                            />
                          )}
                          label={emails.byId[id].configName}
                          labelPlacement="start"
                        />
                      </ListItem>
                    ))}
                  </List>
                </div>
              </Paper>
            </Grid>
          </Grid>
        </Grid>
      )}
      {pagerduties.allIds.length !== 0 && (
        <Grid item xs={4}>
          <Grid container justify="center" spacing={3}>
            <Grid item>
              <Paper className={classes.paper}>
                <Typography>
                  PagerDuty
                </Typography>
                <div
                  style={{ maxHeight: 300, minHeight: 300, overflow: 'auto' }}
                >
                  <List>
                    {pagerduties.allIds.map((id) => (
                      <ListItem key={id}>
                        <FormControlLabel
                          control={(
                            <Checkbox
                              checked={currentConfig.pagerduties.includes(id)}
                              onClick={() => {
                                const payload = {
                                  id,
                                  parentId: currentChain,
                                };
                                if (currentConfig.pagerduties.includes(id)) {
                                  removePagerDutyDetails(payload);
                                } else {
                                  addPagerDutyDetails(payload);
                                }
                              }}
                              name="pagerduties"
                              color="primary"
                            />
                          )}
                          label={pagerduties.byId[id].configName}
                          labelPlacement="start"
                        />
                      </ListItem>
                    ))}
                  </List>
                </div>
              </Paper>
            </Grid>
          </Grid>
        </Grid>
      )}
      {opsgenies.allIds.length !== 0 && (
        <Grid item xs={4}>
          <Grid container justify="center" spacing={3}>
            <Grid item>
              <Paper className={classes.paper}>
                <Typography>
                  OpsGenie
                </Typography>
                <div
                  style={{ maxHeight: 300, minHeight: 300, overflow: 'auto' }}
                >
                  <List>
                    {opsgenies.allIds.map((id) => (
                      <ListItem key={id}>
                        <FormControlLabel
                          control={(
                            <Checkbox
                              checked={currentConfig.opsgenies.includes(id)}
                              onClick={() => {
                                const payload = {
                                  id,
                                  parentId: currentChain,
                                };
                                if (currentConfig.opsgenies.includes(id)) {
                                  removeOpsGenieDetails(payload);
                                } else {
                                  addOpsGenieDetails(payload);
                                }
                              }}
                              name="opsgenies"
                              color="primary"
                            />
                          )}
                          label={opsgenies.byId[id].configName}
                          labelPlacement="start"
                        />
                      </ListItem>
                    ))}
                  </List>
                </div>
              </Paper>
            </Grid>
          </Grid>
        </Grid>
      )}
      <Grid item xs={12} />
      <Grid item xs={2}>
        <Box px={2}>
          <StepButtonContainer
            disabled={false}
            text={BACK}
            navigation={data.channelsTable.backStep}
          />
        </Box>
      </Grid>
      <Grid item xs={8} />
      <Grid item xs={2}>
        <Box px={2}>
          <StepButtonContainer
            disabled={false}
            text={NEXT}
            navigation={data.channelsTable.nextStep}
          />
        </Box>
      </Grid>
    </Grid>
  );
};

ChannelsTable.propTypes = forbidExtraProps({
  telegrams: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      botName: PropTypes.string,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  twilios: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      configName: PropTypes.string,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  emails: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      configName: PropTypes.string,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  pagerduties: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      configName: PropTypes.string,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  opsgenies: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      configName: PropTypes.string,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  config: PropTypes.shape({
    byId: PropTypes.shape({
      telegrams: PropTypes.arrayOf(PropTypes.string),
      twilios: PropTypes.arrayOf(PropTypes.string),
      emails: PropTypes.arrayOf(PropTypes.string),
      pagerduties: PropTypes.arrayOf(PropTypes.string),
      opsgenies: PropTypes.arrayOf(PropTypes.string),
    }).isRequired,
  }).isRequired,
  addTelegramDetails: PropTypes.func.isRequired,
  removeTelegramDetails: PropTypes.func.isRequired,
  addTwilioDetails: PropTypes.func.isRequired,
  removeTwilioDetails: PropTypes.func.isRequired,
  addEmailDetails: PropTypes.func.isRequired,
  removeEmailDetails: PropTypes.func.isRequired,
  addPagerDutyDetails: PropTypes.func.isRequired,
  removePagerDutyDetails: PropTypes.func.isRequired,
  addOpsGenieDetails: PropTypes.func.isRequired,
  removeOpsGenieDetails: PropTypes.func.isRequired,
  currentChain: PropTypes.string.isRequired,
  data: PropTypes.shape({
    channelsTable: PropTypes.shape({
      backStep: PropTypes.string.isRequired,
      nextStep: PropTypes.string.isRequired,
    }).isRequired,
  }).isRequired,
});

export default ChannelsTable;
