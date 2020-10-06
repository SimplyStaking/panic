import React from 'react';
import PropTypes from 'prop-types';
import {
  TextField, Typography, Box, Grid, Switch, FormControlLabel, Button, Tooltip,
} from '@material-ui/core';
import Divider from '@material-ui/core/Divider';
import InfoIcon from '@material-ui/icons/Info';
import { MuiThemeProvider } from '@material-ui/core/styles';
import { NEXT, BACK } from '../../../../constants/constants';
import StepButtonContainer from
  '../../../../containers/chains/general/stepButtonContainer';
import { PingNodeExpoter } from '../../../../utils/buttons';
import { defaultTheme, theme, useStyles } from '../../../theme/default';

const KmsForm = (props) => {
  const classes = useStyles();

  const {
    errors,
    values,
    handleSubmit,
    handleChange,
    setFieldValue,
    data,
  } = props;

  return (
    <MuiThemeProvider theme={defaultTheme}>
      <div>
        <Typography variant="subtitle1" gutterBottom className="greyBackground">
          <Box m={2} p={3}>
            <p>{data.kmsForm.description}</p>
          </Box>
        </Typography>
        <Divider />
        <Box py={4}>
          <form onSubmit={handleSubmit} className={classes.root}>
            <Grid container spacing={3} justify="center" alignItems="center">
              <Grid item xs={2}>
                <Typography> KMS Name: </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  error={!errors.kmsName !== true}
                  value={values.kmsName}
                  type="text"
                  name="kmsName"
                  placeholder={data.kmsForm.nameHolder}
                  helperText={errors.kmsName ? errors.kmsName : ''}
                  onChange={handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={data.kmsForm.nameTip} placement="left">
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
                  error={!errors.exporterUrl !== true}
                  value={values.exporterUrl}
                  type="text"
                  name="exporterUrl"
                  placeholder={data.kmsForm.exporterUrlHolder}
                  helperText={errors.exporterUrl ? errors.exporterUrl : ''}
                  onChange={handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip
                      title={data.kmsForm.exporterUrlTip}
                      placement="left"
                    >
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={2}>
                <Typography> Monitor KMS: </Typography>
              </Grid>
              <Grid item xs={1}>
                <FormControlLabel
                  control={(
                    <Switch
                      checked={values.monitorKms}
                      onClick={() => {
                        setFieldValue('monitorKms', !values.monitorKms);
                      }}
                      name="monitorKms"
                      color="primary"
                    />
                  )}
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip
                      title={data.kmsForm.monitorKmsTip}
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
                      disabled={!(Object.keys(errors).length === 0)}
                      exporterUrl={values.exporterUrl}
                    />
                    <Button
                      variant="outlined"
                      size="large"
                      disabled={!(Object.keys(errors).length === 0)}
                      type="submit"
                    >
                      <Box px={2}>
                        Add KMS
                      </Box>
                    </Button>
                  </Box>
                </Grid>
              </Grid>
              <Grid item xs={2}>
                <Box px={2}>
                  <StepButtonContainer
                    disabled={false}
                    text={BACK}
                    navigation={data.kmsForm.backStep}
                  />
                </Box>
              </Grid>
              <Grid item xs={8} />
              <Grid item xs={2}>
                <Box px={2}>
                  <StepButtonContainer
                    disabled={false}
                    text={NEXT}
                    navigation={data.kmsForm.nextStep}
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

KmsForm.propTypes = {
  errors: PropTypes.shape({
    kmsName: PropTypes.string,
    exporterUrl: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    kmsName: PropTypes.string.isRequired,
    exporterUrl: PropTypes.string.isRequired,
    monitorKms: PropTypes.bool.isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
  setFieldValue: PropTypes.func.isRequired,
  data: PropTypes.shape({
    kmsForm: PropTypes.shape({
      description: PropTypes.string.isRequired,
      exporterUrlHolder: PropTypes.string.isRequired,
      nameHolder: PropTypes.string.isRequired,
      nameTip: PropTypes.string.isRequired,
      exporterUrlTip: PropTypes.string.isRequired,
      monitorKmsTip: PropTypes.string.isRequired,
      backStep: PropTypes.string.isRequired,
      nextStep: PropTypes.string.isRequired,
    }).isRequired,
  }).isRequired,
};

export default KmsForm;
