import React from 'react';
import PropTypes from 'prop-types';
import {
  TextField, Typography, Box, Grid, Switch, FormControlLabel, Button, Tooltip,
} from '@material-ui/core';
import Divider from '@material-ui/core/Divider';
import InfoIcon from '@material-ui/icons/Info';
import { MuiThemeProvider } from '@material-ui/core/styles';
import { NEXT, BACK } from '../../../../constants/constants';
import StepButtonContainer from
  '../../../../containers/chains/general/stepButtonContainer';
import { defaultTheme, theme, useStyles } from '../../../theme/default';

const NodesForm = (props) => {
  const classes = useStyles();

  const {
    errors,
    values,
    handleSubmit,
    handleChange,
    setFieldValue,
    data,
  } = props;

  return (
    <MuiThemeProvider theme={defaultTheme}>
      <div>
        <Typography variant="subtitle1" gutterBottom className="greyBackground">
          <Box m={2} p={3}>
            <p>{data.nodeForm.description}</p>
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
                  error={errors.substrateNodeName}
                  value={values.substrateNodeName}
                  type="text"
                  name="substrateNodeName"
                  placeholder={data.nodeForm.nameHolder}
                  helperText={errors.substrateNodeName
                    ? errors.substrateNodeName : ''}
                  onChange={handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={data.nodeForm.nameTip} placement="left">
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
                  value={values.nodeWsUrl}
                  type="text"
                  name="nodeWsUrl"
                  placeholder={data.nodeForm.websocketHolder}
                  onChange={handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip
                      title={data.nodeForm.websocketTip}
                      placement="left"
                    >
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
                  value={values.telemetryUrl}
                  type="text"
                  name="telemetryUrl"
                  placeholder={data.nodeForm.telemetryHolder}
                  onChange={handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip
                      title={data.nodeForm.telemetryTip}
                      placement="left"
                    >
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
                  value={values.prometheusUrl}
                  type="text"
                  name="prometheusUrl"
                  placeholder={data.nodeForm.prometheusHodler}
                  onChange={handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip
                      title={data.nodeForm.prometheusTip}
                      placement="left"
                    >
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
                  value={values.exporterUrl}
                  type="text"
                  name="exporterUrl"
                  placeholder={data.nodeForm.exporterUrlHolder}
                  onChange={handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip
                      title={data.nodeForm.exporterUrlTip}
                      placement="left"
                    >
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
                  placeholder={data.nodeForm.stashAddressHolder}
                  onChange={handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip
                      title={data.nodeForm.stashAddressTip}
                      placement="left"
                    >
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
                    <Tooltip
                      title={data.nodeForm.isValidatorTip}
                      placement="left"
                    >
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
                    <Tooltip
                      title={data.nodeForm.isArchiveTip}
                      placement="left"
                    >
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
                    <Tooltip
                      title={data.nodeForm.monitorNodeTip}
                      placement="left"
                    >
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
                    <Tooltip
                      title={data.nodeForm.useAsDataSourceTip}
                      placement="left"
                    >
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
                        setFieldValue('useAsDataSource',
                          !values.useAsDataSource);
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
                <Grid
                  container
                  direction="row"
                  justify="flex-end"
                  alignItems="center"
                >
                  <Box px={2}>
                    <Button
                      variant="outlined"
                      size="large"
                      disabled={(Object.keys(errors).length !== 0)}
                    >
                      <Box px={2}>
                        Test Node
                      </Box>
                    </Button>
                    <Button
                      variant="outlined"
                      size="large"
                      disabled={(Object.keys(errors).length !== 0)}
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
                    navigation={data.nodeForm.backStep}
                  />
                </Box>
              </Grid>
              <Grid item xs={8} />
              <Grid item xs={2}>
                <Box px={2}>
                  <StepButtonContainer
                    disabled={false}
                    text={NEXT}
                    navigation={data.nodeForm.nextStep}
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
    nodeWsUrl: PropTypes.string,
    telemetryUrl: PropTypes.string,
    prometheusUrl: PropTypes.string,
    exporterUrl: PropTypes.string,
    stashAddress: PropTypes.string,
    isValidator: PropTypes.bool.isRequired,
    monitorNode: PropTypes.bool.isRequired,
    isArchiveNode: PropTypes.bool.isRequired,
    useAsDataSource: PropTypes.bool.isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
  setFieldValue: PropTypes.func.isRequired,
  data: PropTypes.shape({
    nodeForm: PropTypes.shape({
      description: PropTypes.string.isRequired,
      nameHolder: PropTypes.string.isRequired,
      nameTip: PropTypes.string.isRequired,
      websocketHolder: PropTypes.string.isRequired,
      websocketTip: PropTypes.string.isRequired,
      telemetryHolder: PropTypes.string.isRequired,
      telemetryTip: PropTypes.string.isRequired,
      prometheusHodler: PropTypes.string.isRequired,
      prometheusTip: PropTypes.string.isRequired,
      exporterUrlHolder: PropTypes.string.isRequired,
      exporterUrlTip: PropTypes.string.isRequired,
      stashAddressHolder: PropTypes.string.isRequired,
      stashAddressTip: PropTypes.string.isRequired,
      isValidatorTip: PropTypes.string.isRequired,
      isArchiveTip: PropTypes.string.isRequired,
      monitorNodeTip: PropTypes.string.isRequired,
      useAsDataSourceTip: PropTypes.string.isRequired,
      backStep: PropTypes.string.isRequired,
      nextStep: PropTypes.string.isRequired,
    }).isRequired,
  }).isRequired,
};

export default NodesForm;
