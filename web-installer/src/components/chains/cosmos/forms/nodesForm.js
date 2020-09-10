import React from 'react';
import PropTypes from 'prop-types';
import {
  TextField, Typography, Box, Grid, Switch, FormControlLabel, Button,
} from '@material-ui/core';
import { makeStyles } from '@material-ui/core/styles';
import { NEXT, REPOSITORIES_STEP } from '../../../../constants/constants';
import StepButtonContainer from '../../../../containers/chains/cosmos/stepButtonContainer';

const useStyles = makeStyles(() => ({
  root: {
    display: 'flex',
    flexWrap: 'wrap',
    width: '100%',
  },
}));

const NodesForm = (props) => {
  const classes = useStyles();

  const {
    errors,
    values,
    handleSubmit,
    handleChange,
    setFieldValue,
  } = props;

  return (
    <div>
      <form onSubmit={handleSubmit} className={classes.root}>
        <Grid container spacing={3} justify="center" alignItems="center">
          <Grid item xs={2}>
            <Typography> Node Name: </Typography>
          </Grid>
          <Grid item xs={10}>
            <TextField
              error={!errors.cosmosNodeName !== true}
              value={values.cosmosNodeName}
              type="text"
              name="cosmosNodeName"
              placeholder="cosmos-node-1"
              helperText={errors.cosmosNodeName ? errors.cosmosNodeName : ''}
              onChange={handleChange}
              fullWidth
            />
          </Grid>
          <Grid item xs={2}>
            <Typography> Tendermint RPC URL: </Typography>
          </Grid>
          <Grid item xs={10}>
            <TextField
              value={values.tendermintRPCURL}
              type="text"
              name="tendermintRPCURL"
              placeholder="http://122.321.32.12:26657"
              onChange={handleChange}
              fullWidth
            />
          </Grid>
          <Grid item xs={2}>
            <Typography> Cosmos SDK RPC URL: </Typography>
          </Grid>
          <Grid item xs={10}>
            <TextField
              value={values.cosmosRPCURL}
              type="text"
              name="cosmosRPCURL"
              placeholder="http://122.321.32.12:1317"
              onChange={handleChange}
              fullWidth
            />
          </Grid>
          <Grid item xs={2}>
            <Typography> Prometheus Endpoint URL: </Typography>
          </Grid>
          <Grid item xs={10}>
            <TextField
              value={values.prometheusURL}
              type="text"
              name="prometheusURL"
              placeholder="http://122.321.32.12:26660"
              onChange={handleChange}
              fullWidth
            />
          </Grid>
          <Grid item xs={2}>
            <Typography> Node Exporter URL: </Typography>
          </Grid>
          <Grid item xs={10}>
            <TextField
              value={values.exporterURL}
              type="text"
              name="exporterURL"
              placeholder="http://122,.321.32.12:13330"
              onChange={handleChange}
              fullWidth
            />
          </Grid>
          <Grid item xs={3}>
            <Typography> Node is Validator: </Typography>
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
          <Grid item xs={3}>
            <Typography> Is Archive Node: </Typography>
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
          <Grid item xs={3}>
            <Typography> Monitor Node: </Typography>
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
          <Grid item xs={3}>
            <Typography> Use as Data Source: </Typography>
          </Grid>
          <Grid item xs={1}>
            <FormControlLabel
              control={(
                <Switch
                  checked={values.useAsDataSource}
                  onClick={() => {
                    setFieldValue('useAsDataSource', !values.useAsDataSource);
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
            <Grid container direction="row" justify="flex-end" alignItems="center">
              <Box px={2}>
                <Button
                  variant="outlined"
                  size="large"
                  disabled={!(Object.keys(errors).length === 0)}
                >
                  <Box px={2}>
                    Test Node
                  </Box>
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  disabled={!(Object.keys(errors).length === 0)}
                  type="submit"
                >
                  <Box px={2}>
                    Add Node
                  </Box>
                </Button>
              </Box>
            </Grid>
          </Grid>
          <Grid item xs={8} />
          <Grid item xs={4}>
            <Grid container direction="row" justify="flex-end" alignItems="center">
              <Box px={2}>
                <StepButtonContainer
                  disabled={!(Object.keys(errors).length === 0)}
                  text={NEXT}
                  navigation={REPOSITORIES_STEP}
                />
              </Box>
            </Grid>
          </Grid>
        </Grid>
      </form>
    </div>
  );
};

NodesForm.propTypes = {
  errors: PropTypes.shape({
    cosmosNodeName: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    cosmosNodeName: PropTypes.string.isRequired,
    tendermintRPCURL: PropTypes.string,
    cosmosRPCURL: PropTypes.string,
    prometheusURL: PropTypes.string,
    exporterURL: PropTypes.string,
    isValidator: PropTypes.bool.isRequired,
    monitorNode: PropTypes.bool.isRequired,
    isArchiveNode: PropTypes.bool.isRequired,
    useAsDataSource: PropTypes.bool.isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
  setFieldValue: PropTypes.func.isRequired,
};

export default NodesForm;
