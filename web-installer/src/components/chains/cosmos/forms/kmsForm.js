import React from 'react';
import PropTypes from 'prop-types';
import {
  TextField, Typography, Box, Grid, Switch, FormControlLabel, Button,
} from '@material-ui/core';
import { makeStyles } from '@material-ui/core/styles';
import { NEXT, CHANNELS_STEP } from '../../../../constants/constants';
import StepButtonContainer from '../../../../containers/chains/cosmos/stepButtonContainer';

const useStyles = makeStyles(() => ({
  root: {
    display: 'flex',
    flexWrap: 'wrap',
    width: '100%',
  },
}));

const KMSForm = (props) => {
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
            <Typography> KMS Name: </Typography>
          </Grid>
          <Grid item xs={10}>
            <TextField
              error={!errors.kmsName !== true}
              value={values.kmsName}
              type="text"
              name="kmsName"
              placeholder="KMS_1"
              helperText={errors.kmsName ? errors.kmsName : ''}
              onChange={handleChange}
              fullWidth
            />
          </Grid>
          <Grid item xs={2}>
            <Typography> Node Exporter URL: </Typography>
          </Grid>
          <Grid item xs={10}>
            <TextField
              error={!errors.exporterURL !== true}
              value={values.exporterURL}
              type="text"
              name="exporterURL"
              placeholder="http://176.67.65.56:9000"
              helperText={errors.exporterURL ? errors.exporterURL : ''}
              onChange={handleChange}
              fullWidth
            />
          </Grid>
          <Grid item xs={2}>
            <Typography> Monitor KMS: </Typography>
          </Grid>
          <Grid item xs={1}>
            <FormControlLabel
              control={(
                <Switch
                  checked={values.monitorKMS}
                  onClick={() => {
                    setFieldValue('monitorKMS', !values.monitorKMS);
                  }}
                  name="monitorKMS"
                  color="primary"
                />
              )}
            />
          </Grid>
          <Grid item xs={9} />
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
                    Test KMS
                  </Box>
                </Button>
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
          <Grid item xs={8} />
          <Grid item xs={4}>
            <Grid container direction="row" justify="flex-end" alignItems="center">
              <Box px={2}>
                <StepButtonContainer
                  disabled={false}
                  text={NEXT}
                  navigation={CHANNELS_STEP}
                />
              </Box>
            </Grid>
          </Grid>
        </Grid>
      </form>
    </div>
  );
};

KMSForm.propTypes = {
  errors: PropTypes.shape({
    kmsName: PropTypes.string,
    exporterURL: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    kmsName: PropTypes.string.isRequired,
    exporterURL: PropTypes.string.isRequired,
    monitorKMS: PropTypes.bool.isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
  setFieldValue: PropTypes.func.isRequired,
};

export default KMSForm;
