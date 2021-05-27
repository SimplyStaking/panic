import React from 'react';
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
import { PingNodeExporter } from 'utils/buttons';
import { defaultTheme, theme } from 'components/theme/default';
import Button from 'components/material_ui/CustomButtons/Button';
import useStyles from 'assets/jss/material-kit-react/views/landingPageSections/productStyle';
import CssTextField from 'assets/jss/custom-jss/CssTextField';
import GridContainer from 'components/material_ui/Grid/GridContainer';
import GridItem from 'components/material_ui/Grid/GridItem';

const NodesForm = ({
  errors, values, handleSubmit, handleChange, setFieldValue, data,
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
              <Grid container spacing={3} justify="center" alignItems="center">
                <Grid item xs={12}>
                  <CssTextField
                    id="chain-name-outlined-full-width"
                    error={!!(errors.name)}
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
                    id="node-ws-outlined-full-width"
                    value={values.node_ws_url}
                    label="Node WS URL"
                    type="text"
                    style={{ margin: 8 }}
                    name="node_ws_url"
                    placeholder={data.nodeForm.websocketHolder}
                    onChange={handleChange}
                    fullWidth
                    disabled
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
                            <Tooltip title={data.nodeForm.websocketTip} placement="left">
                              <InfoIcon />
                            </Tooltip>
                          </MuiThemeProvider>
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>
                <Grid item xs={2}>
                  <Grid container direction="row" justify="flex-end" alignItems="center">
                    <FormControlLabel
                      control={(
                        <Switch
                          checked={values.monitor_ws}
                          onClick={() => {
                            setFieldValue('monitor_ws', !values.monitor_ws);
                          }}
                          name="monitor_ws"
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
                  <Grid container direction="row" justify="flex-end" alignItems="center">
                    <PingNodeExporter disabled exporterUrl="" />
                  </Grid>
                </Grid>
                <Grid item xs={8}>
                  <CssTextField
                    id="telemetry-url-outlined-full-width"
                    value={values.telemetry_url}
                    label="Telemetry URL"
                    type="text"
                    style={{ margin: 8 }}
                    name="telemetry_url"
                    placeholder={data.nodeForm.telemetryHolder}
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
                            <Tooltip title={data.nodeForm.telemetryTip} placement="left">
                              <InfoIcon />
                            </Tooltip>
                          </MuiThemeProvider>
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>
                <Grid item xs={2}>
                  <Grid container direction="row" justify="flex-end" alignItems="center">
                    <FormControlLabel
                      control={(
                        <Switch
                          checked={values.monitor_telemetry}
                          onClick={() => {
                            setFieldValue('monitor_telemetry', !values.monitor_telemetry);
                          }}
                          name="monitor_telemetry"
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
                  <Grid container direction="row" justify="flex-end" alignItems="center">
                    <PingNodeExporter disabled exporterUrl="" />
                  </Grid>
                </Grid>
                <Grid item xs={8}>
                  <CssTextField
                    id="prometheus-url-outlined-full-width"
                    value={values.prometheus_url}
                    label="Prometheus URL"
                    type="text"
                    style={{ margin: 8 }}
                    name="prometheus_url"
                    placeholder={data.nodeForm.prometheusHolder}
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
                  <Grid container direction="row" justify="flex-end" alignItems="center">
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
                  <Grid container direction="row" justify="flex-end" alignItems="center">
                    <PingNodeExporter disabled exporterUrl="" />
                  </Grid>
                </Grid>
                <Grid item xs={8}>
                  <CssTextField
                    id="node-exporter-outlined-full-width"
                    error={!!(errors.exporter_url)}
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
                  <Grid container direction="row" justify="flex-end" alignItems="center">
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
                  <Grid container direction="row" justify="flex-end" alignItems="center">
                    <PingNodeExporter disabled={false} exporterUrl={values.exporter_url} />
                  </Grid>
                </Grid>
                <Grid item xs={8}>
                  <CssTextField
                    id="stash-address-outlined-full-width"
                    value={values.stash_address}
                    label="Stash Address"
                    type="text"
                    style={{ margin: 8 }}
                    name="stash_address"
                    placeholder={data.nodeForm.stashAddressHolder}
                    onChange={handleChange}
                    fullWidth
                    disabled
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
                            <Tooltip title={data.nodeForm.stashAddressTip} placement="left">
                              <InfoIcon />
                            </Tooltip>
                          </MuiThemeProvider>
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>
                <Grid item xs={4} />
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
                  <Grid container justify="flex-start">
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
                  <Grid container justify="flex-start">
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
                  <Grid container justify="flex-start">
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
                  <Grid container justify="flex-start">
                    <MuiThemeProvider theme={theme}>
                      <Tooltip title={data.nodeForm.useAsDataSourceTip} placement="left">
                        <InfoIcon />
                      </Tooltip>
                    </MuiThemeProvider>
                  </Grid>
                </Grid>
                <Grid item xs={4}>
                  <Grid container direction="row" justify="flex-end" alignItems="center">
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
    node_ws_url: PropTypes.string,
    monitor_ws: PropTypes.bool.isRequired,
    telemetry_url: PropTypes.string,
    monitor_telemetry: PropTypes.bool.isRequired,
    prometheus_url: PropTypes.string,
    monitor_prometheus: PropTypes.bool.isRequired,
    exporter_url: PropTypes.string,
    monitor_system: PropTypes.bool.isRequired,
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
};

export default NodesForm;
