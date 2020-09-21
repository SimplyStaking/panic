import React from 'react';
import PropTypes from 'prop-types';
import { makeStyles } from '@material-ui/core/styles';
import {
  Grid, FormControlLabel, Checkbox, List, ListItem, Typography, Box,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import {
  NEXT, ALERTS_STEP, BACK, KMS_STEP,
} from '../../../../constants/constants';
import StepButtonContainer from '../../../../containers/chains/cosmos/stepButtonContainer';

const useStyles = makeStyles({
  table: {
    minWidth: 650,
  },
});

const ChannelsTable = (props) => {
  const classes = useStyles();

  const {
    config,
    telegrams,
    opsgenies,
    emails,
    pagerduties,
    twilios,
    addTelegramDetails,
    removeTelegramDetails,
    addTwilioDetails,
    removeTwilioDetails,
    addEmailDetails,
    removeEmailDetails,
    addPagerDutyDetails,
    removePagerDutyDetails,
    addOpsGenieDetails,
    removeOpsGenieDetails,
  } = props;

  return (
    <Grid container className={classes.root} spacing={2}>
      {telegrams.length !== 0 && (
        <Grid item xs={4}>
          <Grid container justify="center" spacing={3}>
            <Grid item>
              <Paper className={classes.paper}>
                <Typography>
                  Telegram
                </Typography>
                <div style={{ maxHeight: 300, minHeight: 300, overflow: 'auto' }}>
                  <List>
                    {telegrams.map((telegram) => (
                      <ListItem key={telegram.botName}>
                        <FormControlLabel
                          control={(
                            <Checkbox
                              checked={config.telegrams.includes(telegram.botName)}
                              onClick={() => {
                                if (config.telegrams.includes(telegram.botName)) {
                                  removeTelegramDetails(telegram.botName);
                                } else {
                                  addTelegramDetails(telegram.botName);
                                }
                              }}
                              name="telegrams"
                              color="primary"
                            />
                          )}
                          label={telegram.botName}
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
      {twilios.length !== 0 && (
        <Grid item xs={4}>
          <Grid container justify="center" spacing={3}>
            <Grid item>
              <Paper className={classes.paper}>
                <Typography>
                  Twilio
                </Typography>
                <div style={{ maxHeight: 300, minHeight: 300, overflow: 'auto' }}>
                  <List>
                    {twilios.map((twilio) => (
                      <ListItem key={twilio.configName}>
                        <FormControlLabel
                          control={(
                            <Checkbox
                              checked={config.twilios.includes(twilio.configName)}
                              onClick={() => {
                                if (config.twilios.includes(twilio.configName)) {
                                  removeTwilioDetails(twilio.configName);
                                } else {
                                  addTwilioDetails(twilio.configName);
                                }
                              }}
                              name="twilios"
                              color="primary"
                            />
                          )}
                          label={twilio.configName}
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
      {emails.length !== 0 && (
        <Grid item xs={4}>
          <Grid container justify="center" spacing={3}>
            <Grid item>
              <Paper className={classes.paper}>
                <Typography>
                  Email
                </Typography>
                <div style={{ maxHeight: 300, minHeight: 300, overflow: 'auto' }}>
                  <List>
                    {emails.map((email) => (
                      <ListItem key={email.configName}>
                        <FormControlLabel
                          control={(
                            <Checkbox
                              checked={config.emails.includes(email.configName)}
                              onClick={() => {
                                if (config.emails.includes(email.configName)) {
                                  removeEmailDetails(email.configName);
                                } else {
                                  addEmailDetails(email.configName);
                                }
                              }}
                              name="emails"
                              color="primary"
                            />
                          )}
                          label={email.configName}
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
      {pagerduties.length !== 0 && (
        <Grid item xs={4}>
          <Grid container justify="center" spacing={3}>
            <Grid item>
              <Paper className={classes.paper}>
                <Typography>
                  PagerDuty
                </Typography>
                <div style={{ maxHeight: 300, minHeight: 300, overflow: 'auto' }}>
                  <List>
                    {pagerduties.map((pagerduty) => (
                      <ListItem key={pagerduty.configName}>
                        <FormControlLabel
                          control={(
                            <Checkbox
                              checked={config.pagerduties.includes(pagerduty.configName)}
                              onClick={() => {
                                if (config.pagerduties.includes(pagerduty.configName)) {
                                  removePagerDutyDetails(pagerduty.configName);
                                } else {
                                  addPagerDutyDetails(pagerduty.configName);
                                }
                              }}
                              name="pagerduties"
                              color="primary"
                            />
                          )}
                          label={pagerduty.configName}
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
      {opsgenies.length !== 0 && (
        <Grid item xs={4}>
          <Grid container justify="center" spacing={3}>
            <Grid item>
              <Paper className={classes.paper}>
                <Typography>
                  OpsGenie
                </Typography>
                <div style={{ maxHeight: 300, minHeight: 300, overflow: 'auto' }}>
                  <List>
                    {opsgenies.map((opsgenie) => (
                      <ListItem key={opsgenie.configName}>
                        <FormControlLabel
                          control={(
                            <Checkbox
                              checked={config.opsgenies.includes(opsgenie.configName)}
                              onClick={() => {
                                if (config.opsgenies.includes(opsgenie.configName)) {
                                  removeOpsGenieDetails(opsgenie.configName);
                                } else {
                                  addOpsGenieDetails(opsgenie.configName);
                                }
                              }}
                              name="opsgenies"
                              color="primary"
                            />
                          )}
                          label={opsgenie.configName}
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
            navigation={KMS_STEP}
          />
        </Box>
      </Grid>
      <Grid item xs={8} />
      <Grid item xs={2}>
        <Box px={2}>
          <StepButtonContainer
            disabled={false}
            text={NEXT}
            navigation={ALERTS_STEP}
          />
        </Box>
      </Grid>
    </Grid>
  );
};

ChannelsTable.propTypes = {
  telegrams: PropTypes.arrayOf(PropTypes.shape({
    botName: PropTypes.string.isRequired,
  })).isRequired,
  twilios: PropTypes.arrayOf(PropTypes.shape({
    configName: PropTypes.string.isRequired,
  })).isRequired,
  emails: PropTypes.arrayOf(PropTypes.shape({
    configName: PropTypes.string.isRequired,
  })).isRequired,
  pagerduties: PropTypes.arrayOf(PropTypes.shape({
    configName: PropTypes.string.isRequired,
  })).isRequired,
  opsgenies: PropTypes.arrayOf(PropTypes.shape({
    configName: PropTypes.string.isRequired,
  })).isRequired,
  config: PropTypes.shape({
    telegrams: PropTypes.arrayOf(PropTypes.string.isRequired).isRequired,
    twilios: PropTypes.arrayOf(PropTypes.string.isRequired).isRequired,
    emails: PropTypes.arrayOf(PropTypes.string.isRequired).isRequired,
    pagerduties: PropTypes.arrayOf(PropTypes.string.isRequired).isRequired,
    opsgenies: PropTypes.arrayOf(PropTypes.string.isRequired).isRequired,
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
};

export default ChannelsTable;
