import React from 'react';
import PropTypes from 'prop-types';
import {
  Typography, Box, Grid, Switch, FormControlLabel, Tooltip,
  InputAdornment,
} from '@material-ui/core';
import Divider from '@material-ui/core/Divider';
import InfoIcon from '@material-ui/icons/Info';
import { MuiThemeProvider } from '@material-ui/core/styles';
import { PingChainlinkPrometheus } from 'utils/buttons';
import { defaultTheme, theme } from 'components/theme/default';
import { Autocomplete } from '@material-ui/lab';
import Button from 'components/material_ui/CustomButtons/Button';
import useStyles from 'assets/jss/material-kit-react/views/landingPageSections/productStyle';
import CssTextField from 'assets/jss/custom-jss/CssTextField';
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

  const updatePrometheusUrl = (event, prometheusUrl) => {
    setFieldValue('prometheus_url', prometheusUrl);
  };

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
                  <Autocomplete
                    multiple
                    freeSolo
                    options={[]}
                    onChange={updatePrometheusUrl}
                    value={values.prometheus_url}
                    renderInput={(params) => (
                      <CssTextField
                        // eslint-disable-next-line react/jsx-props-no-spreading
                        {...params}
                        id="prometheus-url-outlined-full-width"
                        label="Prometheus URL"
                        type="text"
                        style={{ margin: 8 }}
                        name="prometheus_url"
                        placeholder={data.nodeForm.prometheusHolder}
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
                    />
                  </Grid>
                </Grid>
                <Grid item xs={2}>
                  <Grid container direction="row" justify="flex-end" alignItems="center">
                    <PingChainlinkPrometheus
                      disabled={false}
                      prometheusUrl={values.prometheus_url}
                    />
                  </Grid>
                </Grid>
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
                      <Tooltip
                        title={data.nodeForm.monitorNodeTip}
                        placement="left"
                      >
                        <InfoIcon />
                      </Tooltip>
                    </MuiThemeProvider>
                  </Grid>
                </Grid>
                <Grid item xs={4} />
                <Grid item xs={4}>
                  <Grid
                    container
                    direction="row"
                    justify="flex-end"
                    alignItems="center"
                  >
                    <Box>
                      <Button
                        color="primary"
                        size="md"
                        disabled={Object.keys(errors).length !== 0}
                        type="submit"
                      >
                        Add Node
                      </Button>
                    </Box>
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
    prometheus_url: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    name: PropTypes.string.isRequired,
    prometheus_url: PropTypes.arrayOf(PropTypes.string.isRequired),
    monitor_prometheus: PropTypes.bool.isRequired,
    monitor_node: PropTypes.bool.isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
  setFieldValue: PropTypes.func.isRequired,
  data: PropTypes.shape({
    nodeForm: PropTypes.shape({
      title: PropTypes.string.isRequired,
      description: PropTypes.string.isRequired,
      nameHolder: PropTypes.string.isRequired,
      nameTip: PropTypes.string.isRequired,
      prometheusHolder: PropTypes.string.isRequired,
      prometheusTip: PropTypes.string.isRequired,
      ethereumAddressHolder: PropTypes.string.isRequired,
      monitorNodeTip: PropTypes.string.isRequired,
      backStep: PropTypes.string.isRequired,
      nextStep: PropTypes.string.isRequired,
    }).isRequired,
  }).isRequired,
};

export default NodesForm;
