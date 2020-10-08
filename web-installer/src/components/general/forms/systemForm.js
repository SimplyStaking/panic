import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import {
  TextField, Typography, Box, Grid, Switch, FormControlLabel, Button, Tooltip,
} from '@material-ui/core';
import Divider from '@material-ui/core/Divider';
import InfoIcon from '@material-ui/icons/Info';
import { MuiThemeProvider } from '@material-ui/core/styles';
import {
  NEXT, BACK, REPOSITORIES_STEP, CHAINS_PAGE,
} from '../../../../constants/constants';
import StepButtonContainer from
  '../../../../containers/chains/common/stepButtonContainer';
import NavigationButton from '../../../global/navigationButton';
import { PingNodeExpoter } from '../../../../utils/buttons';
import { defaultTheme, theme, useStyles } from '../../../theme/default';
import Data from '../../../../data/chains';

/*
 * Systems form contains all the information and structure needed to setup
 * a system configuration. Contains functionality to test if the provided system
 * is correct.
 */
const SystemForm = (errors, values, handleSubmit, handleChange, setFieldValue,
  pageChanger,) => {
  const classes = useStyles();

  // Next page is infact returning back to the Chains Setings Page
  // but keeping the name the same for consistency
  function nextPage(page) {
    // Clear the current chain, id we are working on.
    pageChanger({ page });
  }

  return (
    <MuiThemeProvider theme={defaultTheme}>
      <div>
        <Typography variant="subtitle1" gutterBottom className="greyBackground">
          <Box m={2} p={3}>
            <p>{Data.chainName.description}</p>
          </Box>
        </Typography>
        <Divider />
        <Box py={4}>
          <form onSubmit={handleSubmit} className={classes.root}>
            <Grid container spacing={3} justify="center" alignItems="center">
              <Grid item xs={2}>
                <Typography> System Name: </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  error={errors.name}
                  value={values.name}
                  type="text"
                  name="name"
                  placeholder="System_1"
                  helperText={errors.name ? errors.name : ''}
                  onChange={handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={Data.systems.name} placement="left">
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
                  error={errors.exporterUrl}
                  value={values.exporterUrl}
                  type="text"
                  name="exporterUrl"
                  placeholder="http://176.67.65.56:9000"
                  helperText={errors.exporterUrl ? errors.exporterUrl : ''}
                  onChange={handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={Data.systems.exporterUrl} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={2}>
                <Typography> Monitor System: </Typography>
              </Grid>
              <Grid item xs={1}>
                <FormControlLabel
                  control={(
                    <Switch
                      checked={values.monitorSystem}
                      onClick={() => {
                        setFieldValue('monitorSystem', !values.monitorSystem);
                      }}
                      name="monitorSystem"
                      color="primary"
                    />
                  )}
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip
                      title={Data.systems.monitorSystem}
                      placement="left"
                    >
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={8} />
              <Grid item xs={8} />
              <Grid item xs={4}>
                <Grid
                  container
                  direction="row"
                  justify="flex-end"
                  alignItems="center"
                >
                  <Box px={2}>
                    <PingNodeExpoter
                      disabled={(Object.keys(errors).length !== 0)}
                      exporterUrl={values.exporterUrl}
                    />
                    <Button
                      variant="outlined"
                      size="large"
                      disabled={(Object.keys(errors).length !== 0)}
                      type="submit"
                    >
                      <Box px={2}>
                        Add System
                      </Box>
                    </Button>
                  </Box>
                </Grid>
              </Grid>
              <Grid item xs={2}>
                <Box px={2}>
                  <NavigationButton
                    disabled={false}
                    nextPage={nextPage}
                    buttonText={BACK}
                    navigation={CHAINS_PAGE}
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

SystemForm.propTypes = forbidExtraProps({
  errors: PropTypes.shape({
    name: PropTypes.string,
    exporterUrl: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    name: PropTypes.string.isRequired,
    exporterUrl: PropTypes.string.isRequired,
    monitorSystem: PropTypes.bool.isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
  setFieldValue: PropTypes.func.isRequired,
  pageChanger: PropTypes.func.isRequired,
});

export default SystemForm;
