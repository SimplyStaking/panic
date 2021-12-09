import React from 'react';
import PropTypes from 'prop-types';
import {
  Typography, Box, Grid, Switch, FormControlLabel, Tooltip,
  InputAdornment,
} from '@material-ui/core';
import Divider from '@material-ui/core/Divider';
import InfoIcon from '@material-ui/icons/Info';
import { MuiThemeProvider } from '@material-ui/core/styles';
import { PingRPC } from 'utils/buttons';
import { defaultTheme, theme } from 'components/theme/default';
import Button from 'components/material_ui/CustomButtons/Button';
import useStyles from 'assets/jss/material-kit-react/views/landingPageSections/productStyle';
import CssTextField from 'assets/jss/custom-jss/CssTextField';
import GridContainer from 'components/material_ui/Grid/GridContainer';
import GridItem from 'components/material_ui/Grid/GridItem';

let isDirty = false;

const EvmNodesForm = ({
  errors,
  values,
  handleSubmit,
  handleChange,
  setFieldValue,
  data,
  dirty,
  toggleDirtyForm,
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
              <h1 className={classes.title}>{data.evmForm.title}</h1>
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
                {data.evmForm.description}
              </p>
            </Box>
          </Typography>
          <Divider />
          <Box m={2} p={3}>
            <form onSubmit={handleSubmit} className="root">
              <Grid
                container
                spacing={3}
                justifyContent="center"
                alignItems="center"
              >
                <Grid item xs={12}>
                  <CssTextField
                    id="evm-node-name-outlined-full-width"
                    error={!!(errors.name)}
                    value={values.name}
                    label="Node name"
                    type="text"
                    style={{ margin: 8 }}
                    name="name"
                    placeholder={data.evmForm.nameHolder}
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
                            <Tooltip
                              title={data.evmForm.nameTip}
                              placement="left"
                            >
                              <InfoIcon />
                            </Tooltip>
                          </MuiThemeProvider>
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>
                <Grid item xs={10}>
                  <CssTextField
                    id="evm-node-http-url-outlined-full-width"
                    value={values.node_http_url}
                    label="RPC URL"
                    type="text"
                    style={{ margin: 8 }}
                    name="node_http_url"
                    placeholder={data.evmForm.httpUrlHolder}
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
                            <Tooltip
                              title={data.evmForm.httpUrlTip}
                              placement="left"
                            >
                              <InfoIcon />
                            </Tooltip>
                          </MuiThemeProvider>
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>
                <Grid item xs={2}>
                  <Grid
                    container
                    direction="row"
                    justifyContent="flex-end"
                    alignItems="center"
                  >
                    <PingRPC
                      disabled={false}
                      httpUrl={values.node_http_url}
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
                  <Grid container justifyContent="flex-start">
                    <MuiThemeProvider theme={theme}>
                      <Tooltip
                        title={data.evmForm.monitorNodeTip}
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
                    justifyContent="flex-end"
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

EvmNodesForm.propTypes = {
  errors: PropTypes.shape({
    name: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    name: PropTypes.string.isRequired,
    node_http_url: PropTypes.string.isRequired,
    monitor_node: PropTypes.bool.isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
  setFieldValue: PropTypes.func.isRequired,
  toggleDirtyForm: PropTypes.func.isRequired,
  dirty: PropTypes.bool.isRequired,
  data: PropTypes.shape({
    evmForm: PropTypes.shape({
      title: PropTypes.string.isRequired,
      description: PropTypes.string.isRequired,
      nameHolder: PropTypes.string.isRequired,
      nameTip: PropTypes.string.isRequired,
      httpUrlHolder: PropTypes.string.isRequired,
      httpUrlTip: PropTypes.string.isRequired,
      monitorNodeTip: PropTypes.string.isRequired,
      backStep: PropTypes.string.isRequired,
      nextStep: PropTypes.string.isRequired,
    }).isRequired,
  }).isRequired,
};

export default EvmNodesForm;
