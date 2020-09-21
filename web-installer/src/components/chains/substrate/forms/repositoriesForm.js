import React from 'react';
import PropTypes from 'prop-types';
import {
  TextField, Typography, Box, Grid, Switch, FormControlLabel, Button,
} from '@material-ui/core';
import { makeStyles } from '@material-ui/core/styles';
import {
  NEXT, KMS_STEP, BACK, NODES_STEP,
} from '../../../../constants/constants';
import StepButtonContainer from '../../../../containers/chains/substrate/stepButtonContainer';

const useStyles = makeStyles(() => ({
  root: {
    display: 'flex',
    flexWrap: 'wrap',
    width: '100%',
  },
}));

const RepositoriesForm = (props) => {
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
            <Typography> Repository Name: </Typography>
          </Grid>
          <Grid item xs={10}>
            <TextField
              error={!errors.repoName !== true}
              value={values.repoName}
              type="text"
              name="repoName"
              placeholder="paritytech/substrate"
              helperText={errors.repoName ? errors.repoName : ''}
              onChange={handleChange}
              fullWidth
            />
          </Grid>
          <Grid item xs={2}>
            <Typography> Monitor Repository: </Typography>
          </Grid>
          <Grid item xs={1}>
            <FormControlLabel
              control={(
                <Switch
                  checked={values.monitorRepo}
                  onClick={() => {
                    setFieldValue('monitorRepo', !values.monitorRepo);
                  }}
                  name="monitorRepo"
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
                    Test Repository
                  </Box>
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  disabled={!(Object.keys(errors).length === 0)}
                  type="submit"
                >
                  <Box px={2}>
                    Add Repository
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
                navigation={NODES_STEP}
              />
            </Box>
          </Grid>
          <Grid item xs={8} />
          <Grid item xs={2}>
            <Box px={2}>
              <StepButtonContainer
                disabled={false}
                text={NEXT}
                navigation={KMS_STEP}
              />
            </Box>
          </Grid>
        </Grid>
      </form>
    </div>
  );
};

RepositoriesForm.propTypes = {
  errors: PropTypes.shape({
    repoName: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    repoName: PropTypes.string.isRequired,
    monitorRepo: PropTypes.bool.isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
  setFieldValue: PropTypes.func.isRequired,
};

export default RepositoriesForm;
