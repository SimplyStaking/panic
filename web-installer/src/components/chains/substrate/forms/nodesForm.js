import React from 'react';
import PropTypes from 'prop-types';
import forbidExtraProps from 'airbnb-prop-types';
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
import { MuiThemeProvider, makeStyles } from '@material-ui/core/styles';
import { NEXT, BACK } from 'constants/constants';
import StepButtonContainer from 'containers/chains/common/stepButtonContainer';
import { defaultTheme, theme } from 'components/theme/default';
import Button from 'components/material_ui/CustomButtons/Button.js';
import styles from 'assets/jss/material-kit-react/views/landingPageSections/productStyle.js';

import GridContainer from 'components/material_ui/Grid/GridContainer.js';
import GridItem from 'components/material_ui/Grid/GridItem.js';

const useStyles = makeStyles(styles);

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
              <Grid item xs={9}>
                <TextField
                  error={errors.substrate_node_name}
                  value={values.substrate_node_name}
                  type="text"
                  name="substrate_node_name"
                  placeholder={data.nodeForm.nameHolder}
                  helperText={
                    errors.substrate_node_name ? errors.substrate_node_name : ''
                  }
                  onChange={handleChange}
                  inputProps={{ min: 0, style: { textAlign: 'right' } }}
                  autoComplete="off"
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
                <Typography> Node WS URL </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  value={values.node_ws_url}
                  type="text"
                  name="node_ws_url"
                  placeholder={data.nodeForm.websocketHolder}
                  onChange={handleChange}
                  inputProps={{ min: 0, style: { textAlign: 'right' } }}
                  autoComplete="off"
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
                <Typography> Telemetry URL </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  value={values.telemetry_url}
                  type="text"
                  name="telemetry_url"
                  placeholder={data.nodeForm.telemetryHolder}
                  onChange={handleChange}
                  inputProps={{ min: 0, style: { textAlign: 'right' } }}
                  autoComplete="off"
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
                <Typography> Prometheus Endpoint URL </Typography>
              </Grid>
              <Grid item xs={9}>
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
                <Typography> Node Exporter URL </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  value={values.exporter_url}
                  type="text"
                  name="exporter_url"
                  placeholder={data.nodeForm.exporterUrlHolder}
                  onChange={handleChange}
                  inputProps={{ min: 0, style: { textAlign: 'right' } }}
                  autoComplete="off"
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
                <Typography> Stash Address </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  value={values.stash_address}
                  type="text"
                  name="stash_address"
                  placeholder={data.nodeForm.stashAddressHolder}
                  onChange={handleChange}
                  inputProps={{ min: 0, style: { textAlign: 'right' } }}
                  autoComplete="off"
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
              <Grid item xs={12} />
              <br />
              <br />
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
    substrate_node_name: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    substrate_node_name: PropTypes.string.isRequired,
    node_ws_url: PropTypes.string,
    telemetry_url: PropTypes.string,
    prometheus_url: PropTypes.string,
    exporter_url: PropTypes.string,
    stash_address: PropTypes.string,
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
      websocketHolder: PropTypes.string.isRequired,
      websocketTip: PropTypes.string.isRequired,
      telemetryHolder: PropTypes.string.isRequired,
      telemetryTip: PropTypes.string.isRequired,
      prometheusHolder: PropTypes.string.isRequired,
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
});

export default NodesForm;
