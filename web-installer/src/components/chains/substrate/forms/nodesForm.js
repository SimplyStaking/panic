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
import TestButtonWithStatus from 'utils/TestButtonWithStatus';
import { defaultTheme, theme } from 'components/theme/default';
import Button from 'components/material_ui/CustomButtons/Button';
import useStyles from 'assets/jss/material-kit-react/views/landingPageSections/productStyle';
import CssTextField from 'assets/jss/custom-jss/CssTextField';
import GridContainer from 'components/material_ui/Grid/GridContainer';
import GridItem from 'components/material_ui/Grid/GridItem';
import { Autocomplete } from '@material-ui/lab';
import { pingSubstrate, pingPrometheus } from 'utils/data';

let isDirty = false;

const NodesForm = ({
  errors, values, handleSubmit, handleChange, setFieldValue, data, dirty, toggleDirtyForm,
}) => {
  const classes = useStyles();

  if (dirty !== isDirty) {
    isDirty = dirty;
    toggleDirtyForm({ isDirty });
  }

  const updateGovernanceAddresses = (event, governanceAddress) => {
    setFieldValue('governance_addresses', governanceAddress);
  };

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
                    value={values.name}
                    label="Node name"
                    type="text"
                    style={{ margin: 8 }}
                    name="name"
                    placeholder={data.nodeForm.nameHolder}
                    error={!!errors.name}
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
                    error={!!errors.node_ws_url}
                    helperText={errors.node_ws_url ? errors.node_ws_url : ''}
                    fullWidth
                    disabled={!values.monitor_node}
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
                  <Grid container direction="row" justifyContent="flex-end" alignItems="center">
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
                      label="Monitor"
                      labelPlacement="start"
                    />
                  </Grid>
                </Grid>
                <Grid item xs={2}>
                  <Grid container direction="row" justify="flex-end" alignItems="center">
                    <TestButtonWithStatus
                      url={values.node_ws_url}
                      disabled={!values.monitor_node}
                      pingMethod={pingSubstrate}
                    />
                  </Grid>
                </Grid>
                <Grid item xs={8}>
                  <CssTextField
                    id="node-exporter-outlined-full-width"
                    value={values.exporter_url}
                    label="Node Exporter URL"
                    type="text"
                    style={{ margin: 8 }}
                    name="exporter_url"
                    placeholder={data.nodeForm.exporterUrlHolder}
                    error={!!errors.exporter_url && values.monitor_system}
                    helperText={
                      errors.exporter_url && values.monitor_system ? errors.exporter_url : ''
                    }
                    onChange={handleChange}
                    fullWidth
                    disabled={!values.monitor_system}
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
                  <Grid container direction="row" justify="flex-end" alignItems="center">
                    <TestButtonWithStatus
                      disabled={!values.monitor_system}
                      url={values.exporter_url}
                      metric="go_memstats_alloc_bytes_total"
                      pingMethod={pingPrometheus}

                    />
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
                    error={!!errors.stash_address && values.is_validator}
                    helperText={
                      errors.stash_address && values.is_validator ? errors.stash_address : ''
                    }
                    onChange={handleChange}
                    fullWidth
                    disabled={!values.is_validator}
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
                <Grid item xs={2}>
                  <Grid container direction="row" justifyContent="flex-end" alignItems="center">
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
                      label="Validator"
                      labelPlacement="start"
                    />
                  </Grid>
                </Grid>
                <Grid item xs={2} />
                <Grid item xs={8}>
                  <Autocomplete
                    multiple
                    freeSolo
                    options={[]}
                    onChange={updateGovernanceAddresses}
                    value={values.governance_addresses}
                    renderInput={(params) => (
                      <CssTextField
                        // eslint-disable-next-line react/jsx-props-no-spreading
                        {...params}
                        id="governance-addresses-outlined-full-width"
                        label="Governance Address"
                        type="text"
                        style={{ margin: 8 }}
                        name="governance_addresses"
                        placeholder={data.nodeForm.governanceAddressHolder}
                        fullWidth
                        margin="normal"
                        InputLabelProps={{
                          shrink: true,
                        }}
                        variant="outlined"
                        autoComplete="off"
                      />
                    )}
                  />
                </Grid>
                <Grid item xs={4} />
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
                <Grid item xs={2}>
                  <Grid container direction="row" justifyContent="center" alignItems="center">
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
    node_ws_url: PropTypes.string,
    governance_addresses: PropTypes.string,
    stash_address: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    name: PropTypes.string.isRequired,
    node_ws_url: PropTypes.string.isRequired,
    monitor_node: PropTypes.bool.isRequired,
    exporter_url: PropTypes.string.isRequired,
    monitor_system: PropTypes.bool.isRequired,
    governance_addresses: PropTypes.arrayOf(PropTypes.string).isRequired,
    monitor_network: PropTypes.bool.isRequired,
    stash_address: PropTypes.string.isRequired,
    is_validator: PropTypes.bool.isRequired,
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
      websocketHolder: PropTypes.string.isRequired,
      websocketTip: PropTypes.string.isRequired,
      exporterUrlHolder: PropTypes.string.isRequired,
      exporterUrlTip: PropTypes.string.isRequired,
      governanceAddressTip: PropTypes.string.isRequired,
      governanceAddressHolder: PropTypes.string.isRequired,
      stashAddressTip: PropTypes.string.isRequired,
      stashAddressHolder: PropTypes.string.isRequired,
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
