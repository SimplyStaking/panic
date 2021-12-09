import React from 'react';
import PropTypes from 'prop-types';
import {
  Grid,
  FormControlLabel,
  Checkbox,
  Typography,
  Box,
  Table,
  TableBody,
  TableContainer,
  TableHead,
  TableRow,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import { NEXT, BACK } from 'constants/constants';
import StepButtonContainer from 'containers/chains/common/stepButtonContainer';
import useStyles from 'assets/jss/material-kit-react/views/landingPageSections/productStyle';
import GridContainer from 'components/material_ui/Grid/GridContainer';
import GridItem from 'components/material_ui/Grid/GridItem';
import Divider from '@material-ui/core/Divider';
import StyledTableRow from 'assets/jss/custom-jss/StyledTableRow';
import StyledTableCell from 'assets/jss/custom-jss/StyledTableCell';

const ChannelsTable = ({
  data,
  config,
  currentChain,
  telegrams,
  opsgenies,
  emails,
  pagerduties,
  twilios,
  slacks,
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
  addSlackDetails,
  removeSlackDetails,
  createPayload,
}) => {
  const currentConfig = config.byId[currentChain];
  const classes = useStyles();

  return (
    <div>
      <div className={classes.subsection}>
        <GridContainer justifyContent="center">
          <GridItem xs={12} sm={12} md={8}>
            <h1 className={classes.title}>{data.channelsTable.title}</h1>
          </GridItem>
        </GridContainer>
      </div>
      <div className="greyBackground">
        <Typography variant="subtitle1" gutterBottom>
          <Box m={2} pt={3} px={3}>
            <p
              style={{
                fontWeight: '350',
                fontSize: '1.2rem',
              }}
            >
              {data.channelsTable.description}
            </p>
          </Box>
        </Typography>
        <Divider />
        <Box mx={2} px={3} pb={3}>
          <div className={classes.subsection}>
            {telegrams.allIds.length === 0
              && opsgenies.allIds.length === 0
              && emails.allIds.length === 0
              && pagerduties.allIds.length === 0
              && slacks.allIds.length === 0
              && twilios.allIds.length === 0 && (
                <GridContainer justifyContent="center">
                  <GridItem xs={12} sm={12} md={8}>
                    <h1 className={classes.title}>{data.channelsTable.empty}</h1>
                  </GridItem>
                </GridContainer>
            )}
          </div>
          <Grid container spacing={3} className={classes.root}>
            {telegrams.allIds.length !== 0 && (
              <Grid item xs={4}>
                <Paper className={classes.paper}>
                  <TableContainer>
                    <Table className="table" aria-label="telegram-channels-table">
                      <TableHead>
                        <TableRow>
                          <StyledTableCell align="center">Telegram</StyledTableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {telegrams.allIds.map((id) => (
                          <StyledTableRow key={id}>
                            <StyledTableCell key={id} align="right">
                              <FormControlLabel
                                control={(
                                  <Checkbox
                                    checked={telegrams.byId[id].parent_ids.includes(currentChain)}
                                    onClick={() => {
                                      createPayload(
                                        telegrams.byId[id],
                                        currentConfig,
                                        addTelegramDetails,
                                        removeTelegramDetails,
                                      );
                                    }}
                                    name="telegrams"
                                    color="primary"
                                  />
                                )}
                                label={telegrams.byId[id].channel_name}
                                labelPlacement="start"
                              />
                            </StyledTableCell>
                          </StyledTableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Paper>
              </Grid>
            )}
            {slacks.allIds.length !== 0 && (
              <Grid item xs={4}>
                <Paper className={classes.paper}>
                  <TableContainer>
                    <Table className="table" aria-label="slack-channels-table">
                      <TableHead>
                        <TableRow>
                          <StyledTableCell align="center">Slack</StyledTableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {slacks.allIds.map((id) => (
                          <StyledTableRow key={id}>
                            <StyledTableCell key={id} align="right">
                              <FormControlLabel
                                control={(
                                  <Checkbox
                                    checked={slacks.byId[id].parent_ids.includes(currentChain)}
                                    onClick={() => {
                                      createPayload(
                                        slacks.byId[id],
                                        currentConfig,
                                        addSlackDetails,
                                        removeSlackDetails,
                                      );
                                    }}
                                    name="slacks"
                                    color="primary"
                                  />
                                )}
                                label={slacks.byId[id].channel_name}
                                labelPlacement="start"
                              />
                            </StyledTableCell>
                          </StyledTableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Paper>
              </Grid>
            )}
            {twilios.allIds.length !== 0 && (
              <Grid item xs={4}>
                <Paper className={classes.paper}>
                  <TableContainer>
                    <Table className="table" aria-label="twilios-channels-table">
                      <TableHead>
                        <TableRow>
                          <StyledTableCell align="center">Twilio</StyledTableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {twilios.allIds.map((id) => (
                          <StyledTableRow key={id}>
                            <StyledTableCell key={id} align="right">
                              <FormControlLabel
                                control={(
                                  <Checkbox
                                    checked={twilios.byId[id].parent_ids.includes(currentChain)}
                                    onClick={() => {
                                      createPayload(
                                        twilios.byId[id],
                                        currentConfig,
                                        addTwilioDetails,
                                        removeTwilioDetails,
                                      );
                                    }}
                                    name="twilios"
                                    color="primary"
                                  />
                                )}
                                label={twilios.byId[id].channel_name}
                                labelPlacement="start"
                              />
                            </StyledTableCell>
                          </StyledTableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Paper>
              </Grid>
            )}
            {emails.allIds.length !== 0 && (
              <Grid item xs={4}>
                <Paper className={classes.paper}>
                  <TableContainer>
                    <Table className="table" aria-label="emails-channels-table">
                      <TableHead>
                        <TableRow>
                          <StyledTableCell align="center">Email</StyledTableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {emails.allIds.map((id) => (
                          <StyledTableRow key={id}>
                            <StyledTableCell key={id} align="right">
                              <FormControlLabel
                                control={(
                                  <Checkbox
                                    checked={emails.byId[id].parent_ids.includes(currentChain)}
                                    onClick={() => {
                                      createPayload(
                                        emails.byId[id],
                                        currentConfig,
                                        addEmailDetails,
                                        removeEmailDetails,
                                      );
                                    }}
                                    name="emails"
                                    color="primary"
                                  />
                                )}
                                label={emails.byId[id].channel_name}
                                labelPlacement="start"
                              />
                            </StyledTableCell>
                          </StyledTableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Paper>
              </Grid>
            )}
            {pagerduties.allIds.length !== 0 && (
              <Grid item xs={4}>
                <Paper className={classes.paper}>
                  <TableContainer>
                    <Table className="table" aria-label="pagerduties-channels-table">
                      <TableHead>
                        <TableRow>
                          <StyledTableCell align="center">PagerDuty</StyledTableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {pagerduties.allIds.map((id) => (
                          <StyledTableRow key={id}>
                            <StyledTableCell key={id} align="right">
                              <FormControlLabel
                                control={(
                                  <Checkbox
                                    checked={pagerduties.byId[id].parent_ids.includes(currentChain)}
                                    onClick={() => {
                                      createPayload(
                                        pagerduties.byId[id],
                                        currentConfig,
                                        addPagerDutyDetails,
                                        removePagerDutyDetails,
                                      );
                                    }}
                                    name="pagerduties"
                                    color="primary"
                                  />
                                )}
                                label={pagerduties.byId[id].channel_name}
                                labelPlacement="start"
                              />
                            </StyledTableCell>
                          </StyledTableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Paper>
              </Grid>
            )}
            {opsgenies.allIds.length !== 0 && (
              <Grid item xs={4}>
                <Paper className={classes.paper}>
                  <TableContainer>
                    <Table className={classes.paper} aria-label="opsgenies-channels-table">
                      <TableHead>
                        <TableRow>
                          <StyledTableCell align="center">OpsGenie</StyledTableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {opsgenies.allIds.map((id) => (
                          <StyledTableRow key={id}>
                            <StyledTableCell key={id} align="right">
                              <FormControlLabel
                                control={(
                                  <Checkbox
                                    checked={opsgenies.byId[id].parent_ids.includes(currentChain)}
                                    onClick={() => {
                                      createPayload(
                                        opsgenies.byId[id],
                                        currentConfig,
                                        addOpsGenieDetails,
                                        removeOpsGenieDetails,
                                      );
                                    }}
                                    name="opsgenies"
                                    color="primary"
                                  />
                                )}
                                label={opsgenies.byId[id].channel_name}
                                labelPlacement="start"
                              />
                            </StyledTableCell>
                          </StyledTableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Paper>
              </Grid>
            )}
          </Grid>
        </Box>
      </div>
      <Grid container spacing={3}>
        <Grid item xs={12} />
        <Grid item xs={4} />
        <Grid item xs={2}>
          <Box px={2}>
            <StepButtonContainer
              disabled={false}
              text={BACK}
              navigation={data.channelsTable.backStep}
            />
          </Box>
        </Grid>
        <Grid item xs={2}>
          <Box px={2}>
            <StepButtonContainer
              disabled={false}
              text={NEXT}
              navigation={data.channelsTable.nextStep}
            />
          </Box>
        </Grid>
        <Grid item xs={4} />
        <Grid item xs={4} />
      </Grid>
    </div>
  );
};

ChannelsTable.propTypes = {
  telegrams: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      channel_name: PropTypes.string,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  slacks: PropTypes.shape({
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
      telegrams: PropTypes.arrayOf(PropTypes.string),
      twilios: PropTypes.arrayOf(PropTypes.string),
      emails: PropTypes.arrayOf(PropTypes.string),
      pagerduties: PropTypes.arrayOf(PropTypes.string),
      opsgenies: PropTypes.arrayOf(PropTypes.string),
    }).isRequired,
  }).isRequired,
  addTelegramDetails: PropTypes.func.isRequired,
  removeTelegramDetails: PropTypes.func.isRequired,
  addSlackDetails: PropTypes.func.isRequired,
  removeSlackDetails: PropTypes.func.isRequired,
  addTwilioDetails: PropTypes.func.isRequired,
  removeTwilioDetails: PropTypes.func.isRequired,
  addEmailDetails: PropTypes.func.isRequired,
  removeEmailDetails: PropTypes.func.isRequired,
  addPagerDutyDetails: PropTypes.func.isRequired,
  removePagerDutyDetails: PropTypes.func.isRequired,
  addOpsGenieDetails: PropTypes.func.isRequired,
  removeOpsGenieDetails: PropTypes.func.isRequired,
  createPayload: PropTypes.func.isRequired,
  currentChain: PropTypes.string.isRequired,
  data: PropTypes.shape({
    channelsTable: PropTypes.shape({
      title: PropTypes.string.isRequired,
      description: PropTypes.string.isRequired,
      empty: PropTypes.string.isRequired,
      backStep: PropTypes.string.isRequired,
      nextStep: PropTypes.string.isRequired,
    }).isRequired,
  }).isRequired,
};

export default ChannelsTable;
