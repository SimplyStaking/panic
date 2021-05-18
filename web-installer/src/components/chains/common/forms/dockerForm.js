import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import {
  Typography, Box, Grid, Switch, FormControlLabel, Tooltip, Divider,
  InputAdornment,
} from '@material-ui/core';
import InfoIcon from '@material-ui/icons/Info';
import { MuiThemeProvider } from '@material-ui/core/styles';
import { PingDockerHubButton } from 'utils/buttons';
import { defaultTheme, theme } from 'components/theme/default';
import Button from 'components/material_ui/CustomButtons/Button';
import useStyles from 'assets/jss/material-kit-react/views/landingPageSections/productStyle';
import GridContainer from 'components/material_ui/Grid/GridContainer';
import GridItem from 'components/material_ui/Grid/GridItem';
import CssTextField from 'assets/jss/custom-jss/CssTextField';

/*
 * Docker form contains all the information and structure needed to setup
 * a docker configuration. Contains functionality to test if the provided config
 * is correct.
 */

const DockerForm = ({
  errors, values, handleSubmit, handleChange, setFieldValue, data,
}) => {
  const classes = useStyles();

  return (
    <MuiThemeProvider theme={defaultTheme}>
      <div>
        <div className={classes.subsection}>
          <GridContainer justify="center">
            <GridItem xs={12} sm={12} md={8}>
              <h1 className={classes.title}>{data.dockerForm.title}</h1>
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
                {data.dockerForm.description}
              </p>
            </Box>
          </Typography>
          <Divider />
          <Box m={2} p={3}>
            <form onSubmit={handleSubmit} className="root">
              <Grid container spacing={3} justify="center" alignItems="center">
                <Grid item xs={12}>
                  <CssTextField
                    id="docker-name-outlined-full-width"
                    error={errors.name}
                    value={values.name}
                    label="DockerHub Repository Name"
                    type="text"
                    style={{ margin: 8 }}
                    name="name"
                    placeholder={data.dockerForm.nameHolder}
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
                            <Tooltip title={data.dockerForm.nameTip} placement="left">
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
                        checked={values.monitor_docker}
                        onClick={() => {
                          setFieldValue('monitor_docker', !values.monitor_docker);
                        }}
                        name="monitor_docker"
                        color="primary"
                      />
                    )}
                    label="Monitor Repository"
                    labelPlacement="start"
                  />
                </Grid>
                <Grid item xs={1}>
                  <Grid container justify="center">
                    <MuiThemeProvider theme={theme}>
                      <Tooltip title={data.dockerForm.monitorTip} placement="left">
                        <InfoIcon />
                      </Tooltip>
                    </MuiThemeProvider>
                  </Grid>
                </Grid>
                <Grid item xs={4} />
                <Grid item xs={4}>
                  <Grid container direction="row" justify="flex-end" alignItems="center">
                    <Box px={2}>
                      <PingDockerHubButton
                        disabled={Object.keys(errors).length !== 0}
                        name={values.name}
                      />
                      <Button
                        color="primary"
                        size="md"
                        disabled={Object.keys(errors).length !== 0}
                        type="submit"
                      >
                        Add Repo
                      </Button>
                    </Box>
                  </Grid>
                </Grid>
                {/* <Grid item xs={12} />
                <br />
                <br />
                <Grid item xs={4} />
                <Grid item xs={2}>
                  <Box px={2}>
                    <StepButtonContainer
                      disabled={false}
                      text={BACK}
                      navigation={data.dockerForm.backStep}
                    />
                  </Box>
                </Grid>
                <Grid item xs={2}>
                  <Box px={2}>
                    <StepButtonContainer
                      disabled={false}
                      text={NEXT}
                      navigation={data.dockerForm.nextStep}
                    />
                  </Box>
                </Grid>
                <Grid item xs={4} />
                <Grid item xs={12} /> */}
              </Grid>
            </form>
          </Box>
        </div>
      </div>
    </MuiThemeProvider>
  );
};

DockerForm.propTypes = forbidExtraProps({
  errors: PropTypes.shape({
    name: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    name: PropTypes.string.isRequired,
    monitor_docker: PropTypes.bool.isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
  setFieldValue: PropTypes.func.isRequired,
  data: PropTypes.shape({
    dockerForm: PropTypes.shape({
      title: PropTypes.string.isRequired,
      description: PropTypes.string.isRequired,
      nameHolder: PropTypes.string.isRequired,
      nameTip: PropTypes.string.isRequired,
      monitorTip: PropTypes.string.isRequired,
      backStep: PropTypes.string.isRequired,
      nextStep: PropTypes.string.isRequired,
    }).isRequired,
  }).isRequired,
});

export default DockerForm;
