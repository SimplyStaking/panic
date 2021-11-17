import React from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import {
  Typography,
  Box,
  Grid,
  Switch,
  FormControlLabel,
  Tooltip,
  InputAdornment,
} from '@material-ui/core';
import Divider from '@material-ui/core/Divider';
import InfoIcon from '@material-ui/icons/Info';
import { MuiThemeProvider } from '@material-ui/core/styles';
import { PingPrometheus, PingTendermint } from 'utils/buttons';
import { defaultTheme, theme } from 'components/theme/default';
import Button from 'components/material_ui/CustomButtons/Button';
import useStyles from 'assets/jss/material-kit-react/views/landingPageSections/productStyle';
import CssTextField from 'assets/jss/custom-jss/CssTextField';
import GridContainer from 'components/material_ui/Grid/GridContainer';
import GridItem from 'components/material_ui/Grid/GridItem';
import { toggleDirty } from 'redux/actions/pageActions';

let isDirty = false;

const NodesForm = ({
  errors, values, handleSubmit, handleChange, setFieldValue, data, dirty, toggleDirtyForm,
}) => {
  const classes = useStyles();

  if (dirty !== isDirty) {
    isDirty = dirty;
    toggleDirtyForm({ isDirty });
  }

  return (
    <MuiThemeProvider theme={defaultTheme}>
      <div>
        <div className={classes.subsection}>
          <GridContainer justifyContent="center">
            <GridItem xs={12} sm={12} md={8}>
              <h1 className={classes.title}>{data.nodeForm.title}</h1>
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
                {data.nodeForm.description}
              </p>
            </Box>
          </Typography>
          <Divider />
          <Box m={2} p={3}>
            <form onSubmit={handleSubmit} className="root">
              <Grid container spacing={3} justifyContent="center" alignItems="center">
                <Grid item xs={12}>
                  <CssTextField
                    id="chain-name-outlined-full-width"
                    error={!!errors.name}
                    value={values.name}
                    label="Node name"
                    type="text"
                    style={{ margin: 8 }}
                    name="name"
                    placeholder={data.nodeForm.nameHolder}
                    helperText={errors.name ? errors.name : ''}
                    onChange={handleChange}
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
                          <MuiThemeProvider theme={theme}>
                            <Tooltip title={data.nodeForm.nameTip} placement="left">
                              <InfoIcon />
                            </Tooltip>
                          </MuiThemeProvider>
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>
                <Grid item xs={8}>
                  <CssTextField
                    id="tendermint-name-outlined-full-width"
                    value={values.tendermint_rpc_url}
                    label="Tendermint RPC URL"
                    type="text"
                    style={{ margin: 8 }}
                    name="tendermint_rpc_url"
                    placeholder={data.nodeForm.tendermintHolder}
                    helperText={errors.name ? errors.name : ''}
                    onChange={handleChange}
                    fullWidth
                    margin="normal"
                    disabled
                    InputLabelProps={{
                      shrink: true,
                    }}
                    variant="outlined"
                    autoComplete="off"
                    InputProps={{
                      endAdornment: (
                        <InputAdornment position="end">
                          <MuiThemeProvider theme={theme}>
                            <Tooltip title={data.nodeForm.tendermintTip} placement="left">
                              <InfoIcon />
                            </Tooltip>
                          </MuiThemeProvider>
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>
                <Grid item xs={2}>
                  <Grid container direction="row" justifyContent="flex-end" alignItems="center">
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
                      label="Monitor"
                      labelPlacement="start"
                      disabled
                    />
                  </Grid>
                </Grid>
                <Grid item xs={2}>
                  <Grid container direction="row" justifyContent="flex-end" alignItems="center">
                    <PingTendermint disabled tendermintRpcUrl={values.tendermint_rpc_url} />
                  </Grid>
                </Grid>
                <Grid item xs={8}>
                  <CssTextField
                    id="cosmos-rest-server-outlined-full-width"
                    value={values.cosmos_rpc_url}
                    label="Cosmos Rest Server"
                    type="text"
                    style={{ margin: 8 }}
                    name="cosmos_rpc_url"
                    placeholder={data.nodeForm.sdkHolder}
                    onChange={handleChange}
                    fullWidth
                    margin="normal"
                    disabled
                    InputLabelProps={{
                      shrink: true,
                    }}
                    variant="outlined"
                    autoComplete="off"
                    InputProps={{
                      endAdornment: (
                        <InputAdornment position="end">
                          <MuiThemeProvider theme={theme}>
                            <Tooltip title={data.nodeForm.sdkTip} placement="left">
                              <InfoIcon />
                            </Tooltip>
                          </MuiThemeProvider>
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>
                <Grid item xs={2}>
                  <Grid container direction="row" justifyContent="flex-end" alignItems="center">
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
                      label="Monitor"
                      labelPlacement="start"
                      disabled
                    />
                  </Grid>
                </Grid>
                <Grid item xs={2}>
                  <Grid container direction="row" justifyContent="flex-end" alignItems="center">
                    <PingPrometheus disabled prometheusUrl="" metric="" />
                  </Grid>
                </Grid>
                <Grid item xs={8}>
                  <CssTextField
                    id="channel-name-outlined-full-width"
                    value={values.prometheus_url}
                    label="Prometheus Endpoint URL"
                    type="text"
                    style={{ margin: 8 }}
                    name="prometheus_url"
                    placeholder={data.nodeForm.prometheusHolder}
                    onChange={handleChange}
                    fullWidth
                    margin="normal"
                    InputLabelProps={{
                      shrink: true,
                    }}
                    disabled
                    variant="outlined"
                    autoComplete="off"
                    InputProps={{
                      endAdornment: (
                        <InputAdornment position="end">
                          <MuiThemeProvider theme={theme}>
                            <Tooltip title={data.nodeForm.prometheusTip} placement="left">
                              <InfoIcon />
                            </Tooltip>
                          </MuiThemeProvider>
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>
                <Grid item xs={2}>
                  <Grid container direction="row" justifyContent="flex-end" alignItems="center">
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
                      label="Monitor"
                      labelPlacement="start"
                      disabled
                    />
                  </Grid>
                </Grid>
                <Grid item xs={2}>
                  <Grid container direction="row" justifyContent="flex-end" alignItems="center">
                    <PingPrometheus disabled prometheusUrl={values.prometheus_url} />
                  </Grid>
                </Grid>
                <Grid item xs={8}>
                  <CssTextField
                    id="node-exporter-url-outlined-full-width"
                    error={!!errors.exporter_url}
                    value={values.exporter_url}
                    label="Node Exporter URL"
                    type="text"
                    style={{ margin: 8 }}
                    name="exporter_url"
                    placeholder={data.nodeForm.exporterUrlHolder}
                    helperText={errors.exporter_url ? errors.exporter_url : ''}
                    onChange={handleChange}
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
                          <MuiThemeProvider theme={theme}>
                            <Tooltip title={data.nodeForm.exporterUrlTip} placement="left">
                              <InfoIcon />
                            </Tooltip>
                          </MuiThemeProvider>
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>
                <Grid item xs={2}>
                  <Grid container direction="row" justifyContent="flex-end" alignItems="center">
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
                      label="Monitor"
                      labelPlacement="start"
                    />
                  </Grid>
                </Grid>
                <Grid item xs={2}>
                  <Grid container direction="row" justifyContent="flex-end" alignItems="center">
                    <PingPrometheus
                      disabled={false}
                      prometheusUrl={values.exporter_url}
                      metric="go_memstats_alloc_bytes_total"
                    />
                  </Grid>
                </Grid>
                <Grid item xs={2}>
                  <Box pl={1}>
                    <Typography> Node is Validator </Typography>
                  </Box>
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
                    disabled
                  />
                </Grid>
                <Grid item xs={1}>
                  <Grid container justifyContent="flex-start">
                    <MuiThemeProvider theme={theme}>
                      <Tooltip title={data.nodeForm.isValidatorTip} placement="left">
                        <InfoIcon />
                      </Tooltip>
                    </MuiThemeProvider>
                  </Grid>
                </Grid>
                <Grid item xs={2}>
                  <Typography> Is Archive Node </Typography>
                </Grid>
                <Grid item xs={1}>
                  <FormControlLabel
                    control={(
                      <Switch
                        checked={values.is_archive_node}
                        onClick={() => {
                          setFieldValue('is_archive_node', !values.is_archive_node);
                        }}
                        name="is_archive_node"
                        color="primary"
                      />
                    )}
                    label=""
                    disabled
                  />
                </Grid>
                <Grid item xs={1}>
                  <Grid container justifyContent="flex-start">
                    <MuiThemeProvider theme={theme}>
                      <Tooltip title={data.nodeForm.isArchiveTip} placement="left">
                        <InfoIcon />
                      </Tooltip>
                    </MuiThemeProvider>
                  </Grid>
                </Grid>
                <Grid item xs={4} />
                <Grid item xs={2}>
                  <Box pl={1}>
                    <Typography> Monitor Node </Typography>
                  </Box>
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
                <Grid item xs={1}>
                  <Grid container justifyContent="flex-start">
                    <MuiThemeProvider theme={theme}>
                      <Tooltip title={data.nodeForm.monitorNodeTip} placement="left">
                        <InfoIcon />
                      </Tooltip>
                    </MuiThemeProvider>
                  </Grid>
                </Grid>
                <Grid item xs={2}>
                  <Typography> Use as Data Source </Typography>
                </Grid>
                <Grid item xs={1}>
                  <FormControlLabel
                    control={(
                      <Switch
                        checked={values.use_as_data_source}
                        onClick={() => {
                          setFieldValue('use_as_data_source', !values.use_as_data_source);
                        }}
                        name="use_as_data_source"
                        color="primary"
                      />
                    )}
                    label=""
                    disabled
                  />
                </Grid>
                <Grid item xs={1}>
                  <Grid container justifyContent="flex-start">
                    <MuiThemeProvider theme={theme}>
                      <Tooltip title={data.nodeForm.useAsDataSourceTip} placement="left">
                        <InfoIcon />
                      </Tooltip>
                    </MuiThemeProvider>
                  </Grid>
                </Grid>
                <Grid item xs={2} />
                <Grid item xs={2}>
                  <Grid container direction="row" justifyContent="flex-end" alignItems="center">
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
              </Grid>
            </form>
          </Box>
        </div>
      </div>
    </MuiThemeProvider>
  );
};

NodesForm.propTypes = {
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
  toggleDirtyForm: PropTypes.func.isRequired,
  dirty: PropTypes.bool.isRequired,
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
    }).isRequired,
  }).isRequired,
};

// Functions to be used in the Cosmos Node form to save the form's details
function mapDispatchToProps(dispatch) {
  return {
    toggleDirtyForm: (tog) => dispatch(toggleDirty(tog)),
  };
}

export default connect(null, mapDispatchToProps)(NodesForm);
