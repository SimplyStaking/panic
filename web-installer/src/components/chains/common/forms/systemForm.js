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
import { NEXT, BACK, GENERAL } from 'constants/constants';
import StepButtonContainer from 'containers/chains/common/stepButtonContainer';
import NavigationButton from 'components/global/navigationButton';
import { PingNodeExporter } from 'utils/buttons';
import { defaultTheme, theme } from 'components/theme/default';
import Button from 'components/material_ui/CustomButtons/Button';
import useStyles from 'assets/jss/material-kit-react/views/landingPageSections/productStyle';
import GridContainer from 'components/material_ui/Grid/GridContainer';
import GridItem from 'components/material_ui/Grid/GridItem';

/*
 * Systems form contains all the information and structure needed to setup
 * a system configuration. Contains functionality to test if the provided system
 * is correct.
 */

const SystemForm = ({
  errors, values, handleSubmit, handleChange, setFieldValue, data, pageChanger,
  currentChain,
}) => {
  const classes = useStyles();

  // Next page is in fact returning back to the Chains Settings Page
  // but keeping the name the same for consistency
  function nextPage(page) {
    // Clear the current chain, id we are working on.
    pageChanger({ page });
  }

  return (
    <MuiThemeProvider theme={defaultTheme}>
      <div>
        <div className={classes.subsection}>
          <GridContainer justify="center">
            <GridItem xs={12} sm={12} md={8}>
              <h1 className={classes.title}>{data.systemForm.title}</h1>
            </GridItem>
          </GridContainer>
        </div>
        <Typography variant="subtitle1" gutterBottom className="greyBackground">
          <Box m={2} p={3}>
            <p>{data.systemForm.description}</p>
          </Box>
        </Typography>
        <Divider />
        <Box py={4}>
          <form onSubmit={handleSubmit} className="root">
            <Grid container spacing={3} justify="center" alignItems="center">
              <Grid item xs={2}>
                <Typography> System Name </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  error={errors.name}
                  value={values.name}
                  type="text"
                  name="name"
                  placeholder={data.systemForm.nameHolder}
                  helperText={errors.name ? errors.name : ''}
                  onChange={handleChange}
                  autoComplete="off"
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={data.systemForm.name} placement="left">
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
                  error={errors.exporter_url}
                  value={values.exporter_url}
                  type="text"
                  name="exporter_url"
                  placeholder={data.systemForm.exporterUrlHolder}
                  helperText={errors.exporter_url ? errors.exporter_url : ''}
                  onChange={handleChange}
                  autoComplete="off"
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={data.systemForm.exporterUrl} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={2}>
                <Typography> Monitor System </Typography>
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
                    <Tooltip title={data.systemForm.monitorSystem} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={8} />
              <Grid item xs={8} />
              <Grid item xs={4}>
                <Grid container direction="row" justify="flex-end" alignItems="center">
                  <Box px={2}>
                    <PingNodeExporter
                      disabled={Object.keys(errors).length !== 0}
                      exporterUrl={values.exporter_url}
                    />
                    <Button
                      color="primary"
                      size="md"
                      disabled={Object.keys(errors).length !== 0}
                      type="submit"
                    >
                      Add
                    </Button>
                  </Box>
                </Grid>
              </Grid>
              <Grid item xs={12} />
              <br />
              <br />
              <Grid item xs={4} />
              <Grid item xs={2}>
                <Box px={2}>
                  {
                  currentChain === GENERAL
                    ? (
                      <NavigationButton
                        disabled={false}
                        nextPage={nextPage}
                        buttonText={BACK}
                        navigation={data.systemForm.backStep}
                      />
                    )
                    : (
                      <StepButtonContainer
                        disabled={false}
                        text={BACK}
                        navigation={data.systemForm.backStep}
                      />
                    )
                    }
                </Box>
              </Grid>
              <Grid item xs={2}>
                <Box px={2}>
                  <StepButtonContainer
                    disabled={false}
                    text={NEXT}
                    navigation={data.systemForm.nextStep}
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

SystemForm.propTypes = forbidExtraProps({
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
  pageChanger: PropTypes.func.isRequired,
  currentChain: PropTypes.string.isRequired,
  data: PropTypes.shape({
    systemForm: PropTypes.shape({
      title: PropTypes.string.isRequired,
      description: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
      nameHolder: PropTypes.string.isRequired,
      nameTip: PropTypes.string.isRequired,
      monitorTip: PropTypes.string.isRequired,
      exporterUrlHolder: PropTypes.string.isRequired,
      exporterUrl: PropTypes.string.isRequired,
      monitorSystem: PropTypes.string.isRequired,
      backStep: PropTypes.string.isRequired,
      nextStep: PropTypes.string.isRequired,
    }).isRequired,
  }).isRequired,
});

export default SystemForm;
