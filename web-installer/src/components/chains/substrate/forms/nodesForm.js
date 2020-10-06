import React from 'react';
import PropTypes from 'prop-types';
import {
  TextField, Typography, Box, Grid, Switch, FormControlLabel, Button, Tooltip,
} from '@material-ui/core';
import Divider from '@material-ui/core/Divider';
import InfoIcon from '@material-ui/icons/Info';
import { MuiThemeProvider } from '@material-ui/core/styles';
import {
  CHAINS_STEP, NEXT, REPOSITORIES_STEP, BACK,
} from '../../../../constants/constants';
import StepButtonContainer from '../../../../containers/chains/substrate/stepButtonContainer';
import { defaultTheme, theme, useStyles } from '../../../theme/default';
import Data from '../../../../data/chains';

const NodesForm = (props) => {
  const classes = useStyles();

  const {
    errors,
    values,
    handleSubmit,
    handleChange,
    setFieldValue,
  } = props;

  return (
    <MuiThemeProvider theme={defaultTheme}>
      <div>
        <Typography variant="subtitle1" gutterBottom className="greyBackground">
          <Box m={2} p={3}>
            <p>{Data.nodeDetails.description}</p>
          </Box>
        </Typography>
        <Divider />
        <Box py={4}>
          <form onSubmit={handleSubmit} className={classes.root}>
            <Grid container spacing={3} justify="center" alignItems="center">
              <Grid item xs={2}>
                <Typography> Node Name: </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  error={!errors.substrateNodeName !== true}
                  value={values.substrateNodeName}
                  type="text"
                  name="substrateNodeName"
                  placeholder="polkadot-node-1"
                  helperText={errors.substrateNodeName ? errors.substrateNodeName : ''}
                  onChange={handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={Data.nodeDetails.name} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={2}>
                <Typography> Node WS URL: </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  value={values.nodeWSURL}
                  type="text"
                  name="nodeWSURL"
                  placeholder="ws://122.321.32.12:9944"
                  onChange={handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={Data.nodeDetails.name} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={2}>
                <Typography> Telemetry URL: </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  value={values.telemetryURL}
                  type="text"
                  name="telemetryURL"
                  placeholder="http://122.321.32.12:8000"
                  onChange={handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={Data.nodeDetails.name} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={2}>
                <Typography> Prometheus Endpoint URL: </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  value={values.prometheusURL}
                  type="text"
                  name="prometheusURL"
                  placeholder="http://122.321.32.12:26660"
                  onChange={handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={Data.nodeDetails.name} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={2}>
                <Typography> Node Exporter URL: </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  value={values.exporterURL}
                  type="text"
                  name="exporterURL"
                  placeholder="http://122,.321.32.12:13330"
                  onChange={handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={Data.nodeDetails.name} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={2}>
                <Typography> Stash Address: </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  value={values.stashAddress}
                  type="text"
                  name="stashAddress"
                  placeholder="EDDJBTFGdsg0gh8sd0sdfs"
                  onChange={handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={Data.nodeDetails.name} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={2}>
                <Typography> Node is Validator: </Typography>
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={Data.nodeDetails.name} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={1}>
                <FormControlLabel
                  control={(
                    <Switch
                      checked={values.isValidator}
                      onClick={() => {
                        setFieldValue('isValidator', !values.isValidator);
                      }}
                      name="isValidator"
                      color="primary"
                    />
                  )}
                />
              </Grid>
              <Grid item xs={2}>
                <Typography> Is Archive Node: </Typography>
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={Data.nodeDetails.name} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={1}>
                <FormControlLabel
                  control={(
                    <Switch
                      checked={values.isArchiveNode}
                      onClick={() => {
                        setFieldValue('isArchiveNode', !values.isArchiveNode);
                      }}
                      name="isArchiveNode"
                      color="primary"
                    />
                  )}
                />
              </Grid>
              <Grid item xs={4} />
              <Grid item xs={2}>
                <Typography> Monitor Node: </Typography>
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={Data.nodeDetails.name} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={1}>
                <FormControlLabel
                  control={(
                    <Switch
                      checked={values.monitorNode}
                      onClick={() => {
                        setFieldValue('monitorNode', !values.monitorNode);
                      }}
                      name="monitorNode"
                      color="primary"
                    />
                  )}
                />
              </Grid>
              <Grid item xs={2}>
                <Typography> Use as Data Source: </Typography>
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={Data.nodeDetails.name} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={1}>
                <FormControlLabel
                  control={(
                    <Switch
                      checked={values.useAsDataSource}
                      onClick={() => {
                        setFieldValue('useAsDataSource', !values.useAsDataSource);
                      }}
                      name="useAsDataSource"
                      color="primary"
                    />
                  )}
                />
              </Grid>
              <Grid item xs={4} />
              <Grid item xs={8} />
              <Grid item xs={4}>
                <Grid container direction="row" justify="flex-end" alignItems="center">
                  <Box px={2}>
                    <Button
                      variant="outlined"
                      size="large"
                      disabled={!(Object.keys(errors).length === 0)}
                    >
                      <Box px={2}>
                        Test Node
                      </Box>
                    </Button>
                    <Button
                      variant="outlined"
                      size="large"
                      disabled={!(Object.keys(errors).length === 0)}
                      type="submit"
                    >
                      <Box px={2}>
                        Add Node
                      </Box>
                    </Button>
                  </Box>
                </Grid>
              </Grid>
              <Grid item xs={2}>
                <Box px={2}>
                  <StepButtonContainer
                    disabled={false}
                    text={BACK}
                    navigation={CHAINS_STEP}
                  />
                </Box>
              </Grid>
              <Grid item xs={8} />
              <Grid item xs={2}>
                <Box px={2}>
                  <StepButtonContainer
                    disabled={false}
                    text={NEXT}
                    navigation={REPOSITORIES_STEP}
                  />
                </Box>
              </Grid>
            </Grid>
          </form>
        </Box>
      </div>
    </MuiThemeProvider>
  );
};

NodesForm.propTypes = {
  errors: PropTypes.shape({
    substrateNodeName: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    substrateNodeName: PropTypes.string.isRequired,
    nodeWSURL: PropTypes.string,
    telemetryURL: PropTypes.string,
    prometheusURL: PropTypes.string,
    exporterURL: PropTypes.string,
    stashAddress: PropTypes.string,
    isValidator: PropTypes.bool.isRequired,
    monitorNode: PropTypes.bool.isRequired,
    isArchiveNode: PropTypes.bool.isRequired,
    useAsDataSource: PropTypes.bool.isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
  setFieldValue: PropTypes.func.isRequired,
};

export default NodesForm;
