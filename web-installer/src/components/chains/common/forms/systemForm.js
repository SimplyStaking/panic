import React from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import {
  Typography, Box, Grid, Switch, FormControlLabel, Tooltip,
  InputAdornment,
} from '@material-ui/core';
import Divider from '@material-ui/core/Divider';
import InfoIcon from '@material-ui/icons/Info';
import { MuiThemeProvider } from '@material-ui/core/styles';
import { PingPrometheus } from 'utils/buttons';
import { defaultTheme, theme } from 'components/theme/default';
import Button from 'components/material_ui/CustomButtons/Button';
import useStyles from 'assets/jss/material-kit-react/views/landingPageSections/productStyle';
import GridContainer from 'components/material_ui/Grid/GridContainer';
import GridItem from 'components/material_ui/Grid/GridItem';
import CssTextField from 'assets/jss/custom-jss/CssTextField';
import { toggleDirty } from 'redux/actions/pageActions';

let isDirty = false;

/*
 * Systems form contains all the information and structure needed to setup
 * a system configuration. Contains functionality to test if the provided system
 * is correct.
 */

const SystemForm = ({
  errors,
  values,
  handleSubmit,
  handleChange,
  setFieldValue,
  data, dirty, toggleDirtyForm,
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
              <h1 className={classes.title}>{data.systemForm.title}</h1>
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
                {data.systemForm.description}
              </p>
            </Box>
          </Typography>
          <Divider />
          <Box m={2} p={3}>
            <form onSubmit={handleSubmit} className="root">
              <Grid container spacing={3} justifyContent="center" alignItems="center">
                <Grid item xs={12}>
                  <CssTextField
                    id="system-name-outlined-full-width"
                    error={!!(errors.name)}
                    value={values.name}
                    label="System Name"
                    type="text"
                    style={{ margin: 8 }}
                    name="name"
                    placeholder={data.systemForm.nameHolder}
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
                            <Tooltip title={data.systemForm.nameTip} placement="left">
                              <InfoIcon />
                            </Tooltip>
                          </MuiThemeProvider>
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>
                <Grid item xs={12}>
                  <CssTextField
                    id="node-exporter-url-outlined-full-width"
                    error={!!(errors.exporter_url)}
                    value={values.exporter_url}
                    label="Node Exporter URL"
                    type="text"
                    style={{ margin: 8 }}
                    name="exporter_url"
                    placeholder={data.systemForm.exporterUrlHolder}
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
                            <Tooltip title={data.systemForm.exporterUrl} placement="left">
                              <InfoIcon />
                            </Tooltip>
                          </MuiThemeProvider>
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>
                <Grid item xs={3}>
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
                    label="Monitor System"
                    labelPlacement="start"
                  />
                </Grid>
                <Grid item xs={1}>
                  <Grid container justifyContent="flex-start">
                    <MuiThemeProvider theme={theme}>
                      <Tooltip title={data.systemForm.monitorSystemTip} placement="left">
                        <InfoIcon />
                      </Tooltip>
                    </MuiThemeProvider>
                  </Grid>
                </Grid>
                <Grid item xs={4} />
                <Grid item xs={4}>
                  <Grid container direction="row" justifyContent="flex-end" alignItems="center">
                    <PingPrometheus
                      disabled={Object.keys(errors).length !== 0}
                      prometheusUrl={values.exporter_url}
                      metric="go_memstats_alloc_bytes_total"
                    />
                    <Button
                      color="primary"
                      size="md"
                      disabled={Object.keys(errors).length !== 0}
                      type="submit"
                    >
                      Add
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

SystemForm.propTypes = {
  errors: PropTypes.shape({
    name: PropTypes.string,
    exporter_url: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    name: PropTypes.string.isRequired,
    exporter_url: PropTypes.string.isRequired,
    monitor_system: PropTypes.bool.isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
  setFieldValue: PropTypes.func.isRequired,
  toggleDirtyForm: PropTypes.func.isRequired,
  dirty: PropTypes.bool.isRequired,
  data: PropTypes.shape({
    systemForm: PropTypes.shape({
      title: PropTypes.string.isRequired,
      description: PropTypes.string.isRequired,
      nameHolder: PropTypes.string.isRequired,
      nameTip: PropTypes.string.isRequired,
      monitorTip: PropTypes.string.isRequired,
      exporterUrlHolder: PropTypes.string.isRequired,
      exporterUrl: PropTypes.string.isRequired,
      monitorSystemTip: PropTypes.string.isRequired,
      backStep: PropTypes.string.isRequired,
      nextStep: PropTypes.string.isRequired,
    }).isRequired,
  }).isRequired,
};

// Functions to be used in the Cosmos Node form to save the form's details
function mapDispatchToProps(dispatch) {
  return {
    toggleDirtyForm: (tog) => dispatch(toggleDirty(tog)),
  };
}

export default connect(null, mapDispatchToProps)(SystemForm);
