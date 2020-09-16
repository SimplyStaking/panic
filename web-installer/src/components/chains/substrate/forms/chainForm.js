import React from 'react';
import PropTypes from 'prop-types';
import {
  TextField, Typography, Box, Grid,
} from '@material-ui/core';
import { makeStyles } from '@material-ui/core/styles';
import {
  NEXT, NODES_STEP, BACK, CHAINS_PAGE,
} from '../../../../constants/constants';
import StepButtonContainer from '../../../../containers/chains/cosmos/stepButtonContainer';
import NavigationButtonContainer from '../../../../containers/global/navigationButtonContainer';

const useStyles = makeStyles(() => ({
  root: {
    display: 'flex',
    flexWrap: 'wrap',
    width: '100%',
  },
}));

const ChainNameForm = (props) => {
  const classes = useStyles();

  const {
    errors,
    handleSubmit,
    handleChange,
    values,
  } = props;

  return (
    <div>
      <form onChange={handleSubmit} className={classes.root}>
        <Grid container spacing={3} justify="center" alignItems="center">
          <Grid item xs={2}>
            <Typography> Chain Name: </Typography>
          </Grid>
          <Grid item xs={10}>
            <TextField
              error={!errors.chainName !== true}
              value={values.chainName}
              type="text"
              name="chainName"
              placeholder="cosmos"
              helperText={errors.chainName ? errors.chainName : ''}
              onChange={handleChange}
              fullWidth
            />
          </Grid>
          <Grid item xs={8} />
          <Grid item xs={4}>
            <Grid container direction="row" justify="flex-end" alignItems="center">
              <Box px={2}>
                <NavigationButtonContainer
                  text={BACK}
                  navigation={CHAINS_PAGE}
                />
              </Box>
              <Box px={2}>
                <StepButtonContainer
                  disabled={!(Object.keys(errors).length === 0)}
                  text={NEXT}
                  navigation={NODES_STEP}
                />
              </Box>
            </Grid>
          </Grid>
        </Grid>
      </form>
    </div>
  );
};

ChainNameForm.propTypes = {
  errors: PropTypes.shape({
    chainName: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    chainName: PropTypes.string.isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
};

export default ChainNameForm;
