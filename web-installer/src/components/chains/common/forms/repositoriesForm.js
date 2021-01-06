import React from 'react';
import PropTypes from 'prop-types';
import{ forbidExtraProps }from 'airbnb-prop-types';
import {
  TextField,
  Typography,
  Box,
  Grid,
  Switch,
  FormControlLabel,
  Tooltip,
  Divider,
} from '@material-ui/core';
import InfoIcon from '@material-ui/icons/Info';
import { MuiThemeProvider, makeStyles } from '@material-ui/core/styles';
import { NEXT, BACK } from 'constants/constants';
import StepButtonContainer from 'containers/chains/common/stepButtonContainer';
import { PingRepoButton } from 'utils/buttons';
import { defaultTheme, theme } from 'components/theme/default';
import Button from 'components/material_ui/CustomButtons/Button.js';
import styles from 'assets/jss/material-kit-react/views/landingPageSections/productStyle.js';
import GridContainer from 'components/material_ui/Grid/GridContainer.js';
import GridItem from 'components/material_ui/Grid/GridItem.js';

/*
 * Repositories form contains all the information and structure needed to setup
 * a repo configuration. Contains functionality to test if the provided repo
 * is correct.
 */

const useStyles = makeStyles(styles);

const RepositoriesForm = ({
  errors, values, handleSubmit, handleChange, setFieldValue, data,
}) => {
  const classes = useStyles();

  return (
    <MuiThemeProvider theme={defaultTheme}>
      <div>
        <div className={classes.subsection}>
          <GridContainer justify="center">
            <GridItem xs={12} sm={12} md={8}>
              <h1 className={classes.title}>{data.repoForm.title}</h1>
            </GridItem>
          </GridContainer>
        </div>
        <Typography variant="subtitle1" gutterBottom className="greyBackground">
          <Box m={2} p={3}>
            <p>{data.repoForm.description}</p>
          </Box>
        </Typography>
        <Divider />
        <Box py={4}>
          <form onSubmit={handleSubmit} className="root">
            <Grid container spacing={3} justify="center" alignItems="center">
              <Grid item xs={2}>
                <Typography> Repository Name </Typography>
              </Grid>
              <Grid item xs={9}>
                <TextField
                  error={errors.repo_name}
                  value={values.repo_name}
                  type="text"
                  name="repo_name"
                  placeholder={data.repoForm.nameHolder}
                  helperText={errors.repo_name ? errors.repo_name : ''}
                  onChange={handleChange}
                  inputProps={{ min: 0, style: { textAlign: 'right' } }}
                  autoComplete="off"
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
                <Typography> Monitor Repository </Typography>
              </Grid>
              <Grid item xs={1}>
                <FormControlLabel
                  control={(
                    <Switch
                      checked={values.monitor_repo}
                      onClick={() => {
                        setFieldValue('monitor_repo', !values.monitor_repo);
                      }}
                      name="monitor_repo"
                      color="primary"
                    />
                  )}
                  label=""
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
                <Grid container direction="row" justify="flex-end" alignItems="center">
                  <Box px={2}>
                    <PingRepoButton
                      disabled={Object.keys(errors).length !== 0}
                      repo={values.repo_name}
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
              <Grid item xs={12} />
              <br />
              <br />
              <Grid item xs={4} />
              <Grid item xs={2}>
                <Box px={2}>
                  <StepButtonContainer
                    disabled={false}
                    text={BACK}
                    navigation={data.repoForm.backStep}
                  />
                </Box>
              </Grid>
              <Grid item xs={2}>
                <Box px={2}>
                  <StepButtonContainer
                    disabled={false}
                    text={NEXT}
                    navigation={data.repoForm.nextStep}
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

RepositoriesForm.propTypes = forbidExtraProps({
  errors: PropTypes.shape({
    repo_name: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    repo_name: PropTypes.string.isRequired,
    monitor_repo: PropTypes.bool.isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
  setFieldValue: PropTypes.func.isRequired,
  data: PropTypes.shape({
    repoForm: PropTypes.shape({
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

export default RepositoriesForm;
