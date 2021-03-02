import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import {
  TextField,
  Typography,
  Box,
  Grid,
  Switch,
  FormControlLabel,
  Tooltip,
} from '@material-ui/core';
import Divider from '@material-ui/core/Divider';
import InfoIcon from '@material-ui/icons/Info';
import { MuiThemeProvider } from '@material-ui/core/styles';
import { NEXT, BACK } from 'constants/constants';
import StepButtonContainer from 'containers/chains/common/stepButtonContainer';
import { PingPrometheus, PingTendermint, PingNodeExporter } from 'utils/buttons';
import { defaultTheme, theme } from 'components/theme/default';
import Button from 'components/material_ui/CustomButtons/Button';
import useStyles from 'assets/jss/material-kit-react/views/landingPageSections/productStyle';

import GridContainer from 'components/material_ui/Grid/GridContainer';
import GridItem from 'components/material_ui/Grid/GridItem';


const NodesForm = ({
  errors,
  values,
  handleSubmit,
  handleChange,
  setFieldValue,
  data,
}) => {
  const classes = useStyles();

  return (
    <MuiThemeProvider theme={defaultTheme}>
      <div>
        <div className={classes.subsection}>
          <GridContainer justify="center">
            <GridItem xs={12} sm={12} md={8}>
              <h1 className={classes.title}>{data.nodeForm.title}</h1>
            </GridItem>
          </GridContainer>
        </div>
        <Typography variant="subtitle1" gutterBottom className="greyBackground">
          <Box m={2} p={3}>
            <p>{data.nodeForm.description}</p>
          </Box>
        </Typography>
        <Divider />
        <Box py={4}>
          <form onSubmit={handleSubmit} className="root">
            <Grid container spacing={3} justify="center" alignItems="center">
              <Grid item xs={2}>
                <Typography> Node Name </Typography>
              </Grid>
              <Grid item xs={5}>
                <TextField
                  error={errors.name}
                  value={values.name}
                  type="text"
                  name="name"
                  placeholder={data.nodeForm.nameHolder}
                  helperText={
                    errors.name ? errors.name : ''
                  }
                  onChange={handleChange}
                  inputProps={{ min: 0, style: { textAlign: 'right' } }}
                  autoComplete="off"
                  fullWidth
                />
              </Grid>
              <Grid item xs={2} />
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={data.nodeForm.nameTip} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={2} />
              <Grid item xs={2}>
                <Typography> Tendermint RPC URL </Typography>
              </Grid>
              <Grid item xs={5}>
                <TextField
                  value={values.tendermint_rpc_url}
                  type="text"
                  name="tendermint_rpc_url"
                  placeholder={data.nodeForm.tendermintHolder}
                  onChange={handleChange}
                  inputProps={{ min: 0, style: { textAlign: 'right' } }}
                  autoComplete="off"
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Typography> Monitor </Typography>
              </Grid>
              <Grid item xs={1}>
                <FormControlLabel
                  control={(
                    <Switch
                      checked={values.monitor_tendermint}
                      onClick={() => {
                        setFieldValue('monitor_tendermint', !values.monitor_tendermint);
                      }}
                      name="monitor_tendermint"
                      color="primary"
                    />
                  )}
                  label=""
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip
                      title={data.nodeForm.tendermintTip}
                      placement="left"
                    >
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={2}>
                <PingTendermint
                  disabled={false}
                  tendermintRpcUrl={values.tendermint_rpc_url}
                />
              </Grid>
              <Grid item xs={2}>
                <Typography> Cosmos Rest Server </Typography>
              </Grid>
              <Grid item xs={5}>
                <TextField
                  value={values.cosmos_rpc_url}
                  type="text"
                  name="cosmos_rpc_url"
                  placeholder={data.nodeForm.sdkHolder}
                  onChange={handleChange}
                  inputProps={{ min: 0, style: { textAlign: 'right' } }}
                  autoComplete="off"
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Typography> Monitor </Typography>
              </Grid>
              <Grid item xs={1}>
                <FormControlLabel
                  control={(
                    <Switch
                      checked={values.monitor_rpc}
                      onClick={() => {
                        setFieldValue('monitor_rpc', !values.monitor_rpc);
                      }}
                      name="monitor_rpc"
                      color="primary"
                    />
                  )}
                  label=""
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={data.nodeForm.sdkTip} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={2}>
                <PingNodeExporter
                  disabled={true}
                  exporterUrl={""}
                />
              </Grid>
              <Grid item xs={2}>
                <Typography> Prometheus Endpoint URL </Typography>
              </Grid>
              <Grid item xs={5}>
                <TextField
                  value={values.prometheus_url}
                  type="text"
                  name="prometheus_url"
                  placeholder={data.nodeForm.prometheusHolder}
                  onChange={handleChange}
                  inputProps={{ min: 0, style: { textAlign: 'right' } }}
                  autoComplete="off"
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Typography> Monitor </Typography>
              </Grid>
              <Grid item xs={1}>
                <FormControlLabel
                  control={(
                    <Switch
                      checked={values.monitor_prometheus}
                      onClick={() => {
                        setFieldValue('monitor_prometheus', !values.monitor_prometheus);
                      }}
                      name="monitor_prometheus"
                      color="primary"
                    />
                  )}
                  label=""
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
                <PingPrometheus
                  disabled={false}
                  prometheusUrl={values.prometheus_url}
                />
              </Grid>
              <Grid item xs={2}>
                <Typography> Node Exporter URL </Typography>
              </Grid>
              <Grid item xs={5}>
                <TextField
                  error={errors.exporter_url}
                  value={values.exporter_url}
                  type="text"
                  name="exporter_url"
                  placeholder={data.nodeForm.exporterUrlHolder}
                  helperText={errors.exporter_url ? errors.exporter_url : ''}
                  onChange={handleChange}
                  inputProps={{ min: 0, style: { textAlign: 'right' } }}
                  autoComplete="off"
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Typography> Monitor </Typography>
              </Grid>
              <Grid item xs={1}>
                <FormControlLabel
                  control={(
                    <Switch
                      checked={values.monitor_system}
                      onClick={() => {
                        setFieldValue('monitor_system', !values.monitor_system);
                      }}
                      name="monitor_system"
                      color="primary"
                    />
                  )}
                  label=""
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
                <PingNodeExporter
                  disabled={false}
                  exporterUrl={values.exporter_url}
                />
              </Grid>
              <Grid item xs={2}>
                <Typography> Node is Validator </Typography>
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
                      checked={values.is_validator}
                      onClick={() => {
                        setFieldValue('is_validator', !values.is_validator);
                      }}
                      name="is_validator"
                      color="primary"
                    />
                  )}
                  label=""
                />
              </Grid>
              <Grid item xs={2}>
                <Typography> Is Archive Node </Typography>
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
                      checked={values.is_archive_node}
                      onClick={() => {
                        setFieldValue(
                          'is_archive_node',
                          !values.is_archive_node,
                        );
                      }}
                      name="is_archive_node"
                      color="primary"
                    />
                  )}
                  label=""
                />
              </Grid>
              <Grid item xs={4} />
              <Grid item xs={2}>
                <Typography> Monitor Node </Typography>
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
                      checked={values.monitor_node}
                      onClick={() => {
                        setFieldValue('monitor_node', !values.monitor_node);
                      }}
                      name="monitor_node"
                      color="primary"
                    />
                  )}
                  label=""
                />
              </Grid>
              <Grid item xs={2}>
                <Typography> Use as Data Source </Typography>
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
                      checked={values.use_as_data_source}
                      onClick={() => {
                        setFieldValue(
                          'use_as_data_source',
                          !values.use_as_data_source,
                        );
                      }}
                      name="use_as_data_source"
                      color="primary"
                    />
                  )}
                  label=""
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
                  <Button
                    color="primary"
                    size="md"
                    disabled={Object.keys(errors).length !== 0}
                    type="submit"
                  >
                    Add Node
                  </Button>
                </Grid>
              </Grid>
              <Grid item xs={12} style={{marginBottom: '150px'}} />
              <Grid item xs={4} />
              <Grid item xs={2}>
                <Box px={2}>
                  <StepButtonContainer
                    disabled={false}
                    text={BACK}
                    navigation={data.nodeForm.backStep}
                  />
                </Box>
              </Grid>
              <Grid item xs={2}>
                <Box px={2}>
                  <StepButtonContainer
                    disabled={false}
                    text={NEXT}
                    navigation={data.nodeForm.nextStep}
                  />
                </Box>
              </Grid>
              <Grid item xs={4} />
              <Grid item xs={12} />
            </Grid>
          </form>
        </Box>
      </div>
    </MuiThemeProvider>
  );
};

NodesForm.propTypes = forbidExtraProps({
  errors: PropTypes.shape({
    name: PropTypes.string,
    exporter_url: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    name: PropTypes.string.isRequired,
    tendermint_rpc_url: PropTypes.string,
    monitor_tendermint: PropTypes.bool.isRequired,
    cosmos_rpc_url: PropTypes.string,
    monitor_rpc: PropTypes.bool.isRequired,
    prometheus_url: PropTypes.string,
    monitor_prometheus: PropTypes.bool.isRequired,
    exporter_url: PropTypes.string,
    monitor_system: PropTypes.bool.isRequired,
    is_validator: PropTypes.bool.isRequired,
    monitor_node: PropTypes.bool.isRequired,
    is_archive_node: PropTypes.bool.isRequired,
    use_as_data_source: PropTypes.bool.isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
  setFieldValue: PropTypes.func.isRequired,
  data: PropTypes.shape({
    nodeForm: PropTypes.shape({
      title: PropTypes.string.isRequired,
      description: PropTypes.string.isRequired,
      nameHolder: PropTypes.string.isRequired,
      nameTip: PropTypes.string.isRequired,
      tendermintHolder: PropTypes.string.isRequired,
      tendermintTip: PropTypes.string.isRequired,
      sdkHolder: PropTypes.string.isRequired,
      sdkTip: PropTypes.string.isRequired,
      prometheusHolder: PropTypes.string.isRequired,
      prometheusTip: PropTypes.string.isRequired,
      exporterUrlHolder: PropTypes.string.isRequired,
      exporterUrlTip: PropTypes.string.isRequired,
      isValidatorTip: PropTypes.string.isRequired,
      isArchiveTip: PropTypes.string.isRequired,
      monitorNodeTip: PropTypes.string.isRequired,
      useAsDataSourceTip: PropTypes.string.isRequired,
      backStep: PropTypes.string.isRequired,
      nextStep: PropTypes.string.isRequired,
    }).isRequired,
  }).isRequired,
});

export default NodesForm;
