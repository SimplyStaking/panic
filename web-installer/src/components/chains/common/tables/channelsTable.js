import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import {
  Grid, FormControlLabel, Checkbox, List, ListItem, Typography, Box,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import { NEXT, BACK } from 'constants/constants';
import StepButtonContainer from 'containers/chains/common/stepButtonContainer';
import styles from "assets/jss/material-kit-react/views/landingPageSections/productStyle.js";
import { makeStyles } from "@material-ui/core/styles";
import GridContainer from "components/material_ui/Grid/GridContainer.js";
import GridItem from "components/material_ui/Grid/GridItem.js";
import Divider from '@material-ui/core/Divider';

const useStyles = makeStyles(styles);

const ChannelsTable = ({data, config, currentChain, telegrams, opsgenies,
  emails, pagerduties, twilios, addTelegramDetails, removeTelegramDetails,
  addTwilioDetails, removeTwilioDetails, addEmailDetails, removeEmailDetails,
  addPagerDutyDetails, removePagerDutyDetails, addOpsGenieDetails,
  removeOpsGenieDetails}) => {

  const currentConfig = config.byId[currentChain];

  const classes = useStyles();

  return (
    <div>
      <div className={classes.subsection}>
        <GridContainer justify="center">
          <GridItem xs={12} sm={12} md={8}>
            <h1 className={classes.title}>
                {data.channelsTable.title}
            </h1>
          </GridItem>
        </GridContainer>
      </div>
      <Typography variant="subtitle1" gutterBottom className="greyBackground">
          <Box m={2} p={3}>
            <p>{data.channelsTable.description}</p>
          </Box>
      </Typography>
      <Divider />
      <div className={classes.subsection}>
        {telegrams.allIds.length === 0 &&
          opsgenies.allIds.length === 0 &&
          emails.allIds.length === 0 &&
          pagerduties.allIds.length === 0 &&
          twilios.allIds.length === 0 && (
            <GridContainer justify="center">
              <GridItem xs={12} sm={12} md={8}>
                <h1 className={classes.title}>
                    {data.channelsTable.empty}
                </h1>
              </GridItem>
            </GridContainer>
          )
        }
      </div>
      <Grid container className="root" spacing={0}>
        {telegrams.allIds.length !== 0 && (
          <Grid item xs={4}>
            <Grid container justify="center" spacing={3}>
              <Grid item>
                <TableContainer component={Paper}>
                  <Table className="table" aria-label="simple table">
                    <TableHead>
                      <TableRow>
                        <TableCell align="center">
                          Telegram
                        </TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {telegrams.allIds.map((id) => (
                        <TableRow key={id}>
                          <TableCell key={id} align="center">
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
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
                <Paper className="paper">
                  <Typography>
                    Telegram
                  </Typography>
                  <div
                    className="tableColumn"
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
                <Paper className="paper">
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
                <Paper className="paper">
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
                <Paper className="paper">
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
                <Paper className="paper">
                  <Typography>
                    OpsGenie
                  </Typography>
                  <div
                    className="tableColumn"
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
    </div>
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
