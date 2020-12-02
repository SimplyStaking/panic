import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import {
  TextField, Typography, Box, Grid, Switch, FormControlLabel, Tooltip,
} from '@material-ui/core';
import Divider from '@material-ui/core/Divider';
import InfoIcon from '@material-ui/icons/Info';
import { MuiThemeProvider } from '@material-ui/core/styles';
import { NEXT, BACK } from 'constants/constants';
import StepButtonContainer from 'containers/chains/common/stepButtonContainer';
import { PingCosmosButton } from 'utils/buttons';
import { defaultTheme, theme } from '../../../theme/default';
import Button from "components/material_ui/CustomButtons/Button.js";
import styles from "assets/jss/material-kit-react/views/landingPageSections/productStyle.js";
import { makeStyles } from "@material-ui/core/styles";
import GridContainer from "components/material_ui/Grid/GridContainer.js";
import GridItem from "components/material_ui/Grid/GridItem.js";

const useStyles = makeStyles(styles);

const NodesForm = ({errors, values, handleSubmit, handleChange, setFieldValue,
  data}) => {

  const classes = useStyles();

  return (
    <MuiThemeProvider theme={defaultTheme}>
      <div>
        <div className={classes.subsection}>
          <GridContainer justify="center">
            <GridItem xs={12} sm={12} md={8}>
              <h1 className={classes.title}>
                  {data.nodeForm.title}
              </h1>
            </GridItem>
          </GridContainer>
        </div>
        <Typography variant="subtitle1" gutterBottom className="greyBackground">
          <Box m={2} p={3}>
            <p>{data.nodeForm.description}</p>
          </Box>
        </Typography>
        <Divider />
        <Box py={4}>
          <form onSubmit={handleSubmit} className="root">
            <Grid container spacing={3} justify="center" alignItems="center">
              <Grid item xs={2}>
                <Typography> Node Name </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  error={errors.cosmosNodeName}
                  value={values.cosmosNodeName}
                  type="text"
                  name="cosmosNodeName"
                  placeholder={data.nodeForm.nameHolder}
                  helperText={errors.cosmosNodeName
                    ? errors.cosmosNodeName : ''}
                  onChange={handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={data.nodeForm.nameTip} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={2}>
                <Typography> Tendermint RPC URL </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  value={values.tendermintRpcUrl}
                  type="text"
                  name="tendermintRpcUrl"
                  placeholder={data.nodeForm.tendermintHolder}
                  onChange={handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip
                      title={data.nodeForm.tendermintTip}
                      placement="left"
                    >
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={2}>
                <Typography> Cosmos Rest Server </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  value={values.cosmosRpcUrl}
                  type="text"
                  name="cosmosRpcUrl"
                  placeholder={data.nodeForm.sdkHolder}
                  onChange={handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={data.nodeForm.sdkTip} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={2}>
                <Typography> Prometheus Endpoint URL </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  value={values.prometheusUrl}
                  type="text"
                  name="prometheusUrl"
                  placeholder={data.nodeForm.prometheusHolder}
                  onChange={handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip
                      title={data.nodeForm.prometheusTip}
                      placement="left"
                    >
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
                  value={values.exporterUrl}
                  type="text"
                  name="exporterUrl"
                  placeholder={data.nodeForm.exporterUrlHolder}
                  onChange={handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip
                      title={data.nodeForm.exporterUrlTip}
                      placement="left"
                    >
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={2}>
                <Typography> Node is Validator </Typography>
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip
                      title={data.nodeForm.isValidatorTip}
                      placement="left"
                    >
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={1}>
                <FormControlLabel
                  control={(
                    <Switch
                      checked={values.isValidator}
                      onClick={() => {
                        setFieldValue('isValidator', !values.isValidator);
                      }}
                      name="isValidator"
                      color="primary"
                    />
                  )}
                />
              </Grid>
              <Grid item xs={2}>
                <Typography> Is Archive Node </Typography>
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip
                      title={data.nodeForm.isArchiveTip}
                      placement="left"
                    >
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={1}>
                <FormControlLabel
                  control={(
                    <Switch
                      checked={values.isArchiveNode}
                      onClick={() => {
                        setFieldValue('isArchiveNode', !values.isArchiveNode);
                      }}
                      name="isArchiveNode"
                      color="primary"
                    />
                  )}
                />
              </Grid>
              <Grid item xs={4} />
              <Grid item xs={2}>
                <Typography> Monitor Node </Typography>
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
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
              <Grid item xs={1}>
                <FormControlLabel
                  control={(
                    <Switch
                      checked={values.monitorNode}
                      onClick={() => {
                        setFieldValue('monitorNode', !values.monitorNode);
                      }}
                      name="monitorNode"
                      color="primary"
                    />
                  )}
                />
              </Grid>
              <Grid item xs={2}>
                <Typography> Use as Data Source </Typography>
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip
                      title={data.nodeForm.useAsDataSourceTip}
                      placement="left"
                    >
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
              </Grid>
              <Grid item xs={1}>
                <FormControlLabel
                  control={(
                    <Switch
                      checked={values.useAsDataSource}
                      onClick={() => {
                        setFieldValue('useAsDataSource',
                          !values.useAsDataSource);
                      }}
                      name="useAsDataSource"
                      color="primary"
                    />
                  )}
                />
              </Grid>
              <Grid item xs={4} />
              <Grid item xs={8} />
              <Grid item xs={4}>
                <Grid
                  container
                  direction="row"
                  justify="flex-end"
                  alignItems="center"
                >
                  <PingCosmosButton
                    disabled={false}
                    tendermintRpcUrl={values.tendermintRpcUrl}
                    prometheusUrl={values.prometheusUrl}
                    exporterUrl={values.exporterUrl}
                  />
                  <Button
                    color="primary"
                    size="md"
                    disabled={(Object.keys(errors).length !== 0)}
                    type="submit"
                  >
                      Add Node
                  </Button>
                </Grid>
              </Grid>
              <Grid item xs={2}>
                <Box px={2}>
                  <StepButtonContainer
                    disabled={false}
                    text={BACK}
                    navigation={data.nodeForm.backStep}
                  />
                </Box>
              </Grid>
              <Grid item xs={8} />
              <Grid item xs={2}>
                <Box px={2}>
                  <StepButtonContainer
                    disabled={false}
                    text={NEXT}
                    navigation={data.nodeForm.nextStep}
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

NodesForm.propTypes = forbidExtraProps({
  errors: PropTypes.shape({
    cosmosNodeName: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    cosmosNodeName: PropTypes.string.isRequired,
    tendermintRpcUrl: PropTypes.string,
    cosmosRpcUrl: PropTypes.string,
    prometheusUrl: PropTypes.string,
    exporterUrl: PropTypes.string,
    isValidator: PropTypes.bool.isRequired,
    monitorNode: PropTypes.bool.isRequired,
    isArchiveNode: PropTypes.bool.isRequired,
    useAsDataSource: PropTypes.bool.isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
  setFieldValue: PropTypes.func.isRequired,
  data: PropTypes.shape({
    nodeForm: PropTypes.shape({
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
      backStep: PropTypes.string.isRequired,
      nextStep: PropTypes.string.isRequired,
    }).isRequired,
  }).isRequired,
});

export default NodesForm;
