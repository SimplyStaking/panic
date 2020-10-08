import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import {
  TextField, Typography, Box, Grid, Switch, FormControlLabel, Button, Tooltip,
} from '@material-ui/core';
import Divider from '@material-ui/core/Divider';
import InfoIcon from '@material-ui/icons/Info';
import { MuiThemeProvider } from '@material-ui/core/styles';
import { NEXT, BACK } from '../../../../constants/constants';
import StepButtonContainer from
  '../../../../containers/chains/common/stepButtonContainer';
import { PingRepoButton } from '../../../../utils/buttons';
import { defaultTheme, theme, useStyles } from '../../../theme/default';

/*
 * Repositories form contains all the information and structure needed to setup
 * a repo configuration. Contains functionality to test if the provided repo
 * is correct.
 */
const RepositoriesForm = ({errors, values, handleSubmit, handleChange,
  setFieldValue, data}) => {
  const classes = useStyles();

  return (
    <MuiThemeProvider theme={defaultTheme}>
      <div>
        <Typography variant="subtitle1" gutterBottom className="greyBackground">
          <Box m={2} p={3}>
            <p>{data.repoForm.description}</p>
          </Box>
        </Typography>
        <Divider />
        <Box py={4}>
          <form onSubmit={handleSubmit} className={classes.root}>
            <Grid container spacing={3} justify="center" alignItems="center">
              <Grid item xs={2}>
                <Typography> Repository Name: </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  error={errors.repoName}
                  value={values.repoName}
                  type="text"
                  name="repoName"
                  placeholder={data.repoForm.nameHolder}
                  helperText={errors.repoName ? errors.repoName : ''}
                  onChange={handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={data.repoForm.nameTip} placement="left">
                      <InfoIcon />
                    </Tooltip>
                  </MuiThemeProvider>
                </Grid>
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
              <Grid item xs={1}>
                <Grid container justify="center">
                  <MuiThemeProvider theme={theme}>
                    <Tooltip title={data.repoForm.monitorTip} placement="left">
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
                    <PingRepoButton
                      disabled={(Object.keys(errors).length !== 0)}
                      repo={values.repoName}
                    />
                    <Button
                      variant="outlined"
                      size="large"
                      disabled={(Object.keys(errors).length !== 0)}
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
                    navigation={data.repoForm.backStep}
                  />
                </Box>
              </Grid>
              <Grid item xs={8} />
              <Grid item xs={2}>
                <Box px={2}>
                  <StepButtonContainer
                    disabled={false}
                    text={NEXT}
                    navigation={data.repoForm.nextStep}
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

RepositoriesForm.propTypes = forbidExtraProps({
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
  data: PropTypes.shape({
    repoForm: PropTypes.shape({
      description: PropTypes.string.isRequired,
      nameHolder: PropTypes.string.isRequired,
      nameTip: PropTypes.string.isRequired,
      monitorTip: PropTypes.string.isRequired,
      backStep: PropTypes.string.isRequired,
      nextStep: PropTypes.string.isRequired,
    }).isRequired,
  }).isRequired,
});

export default RepositoriesForm;
