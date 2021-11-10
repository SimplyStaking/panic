import React from 'react';
import PropTypes from 'prop-types';
import {
  Typography, Box, Grid, Switch, FormControlLabel, Tooltip, Divider,
  InputAdornment,
} from '@material-ui/core';
import InfoIcon from '@material-ui/icons/Info';
import { MuiThemeProvider } from '@material-ui/core/styles';
import { PingRepoButton } from 'utils/buttons';
import { defaultTheme, theme } from 'components/theme/default';
import Button from 'components/material_ui/CustomButtons/Button';
import useStyles from 'assets/jss/material-kit-react/views/landingPageSections/productStyle';
import GridContainer from 'components/material_ui/Grid/GridContainer';
import GridItem from 'components/material_ui/Grid/GridItem';
import CssTextField from 'assets/jss/custom-jss/CssTextField';

/*
 * Repositories form contains all the information and structure needed to setup
 * a repo configuration. Contains functionality to test if the provided repo
 * is correct.
 */

const GithubRepositoriesForm = ({
  errors, values, handleSubmit, handleChange, setFieldValue, data,
}) => {
  const classes = useStyles();

  return (
    <MuiThemeProvider theme={defaultTheme}>
      <div>
        <div className={classes.subsection}>
          <GridContainer justifyContent="center">
            <GridItem xs={12} sm={12} md={8}>
              <h1 className={classes.title}>{data.repoForm.title}</h1>
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
                {data.repoForm.description}
              </p>
            </Box>
          </Typography>
          <Divider />
          <Box m={2} p={3}>
            <form onSubmit={handleSubmit} className="root">
              <Grid container spacing={3} justifyContent="center" alignItems="center">
                <Grid item xs={12}>
                  <CssTextField
                    id="repo-name-outlined-full-width"
                    error={!!(errors.repo_name)}
                    value={values.repo_name}
                    label="Repository Name"
                    type="text"
                    style={{ margin: 8 }}
                    name="repo_name"
                    placeholder={data.repoForm.nameHolder}
                    helperText={errors.repo_name ? errors.repo_name : ''}
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
                            <Tooltip title={data.repoForm.nameTip} placement="left">
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
                        checked={values.monitor_repo}
                        onClick={() => {
                          setFieldValue('monitor_repo', !values.monitor_repo);
                        }}
                        name="monitor_repo"
                        color="primary"
                      />
                    )}
                    label="Monitor Repository"
                    labelPlacement="start"
                  />
                </Grid>
                <Grid item xs={1}>
                  <Grid container justifyContent="center">
                    <MuiThemeProvider theme={theme}>
                      <Tooltip title={data.repoForm.monitorTip} placement="left">
                        <InfoIcon />
                      </Tooltip>
                    </MuiThemeProvider>
                  </Grid>
                </Grid>
                <Grid item xs={4} />
                <Grid item xs={4}>
                  <Grid container direction="row" justifyContent="flex-end" alignItems="center">
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
                  </Grid>
                </Grid>
              </Grid>
            </form>
          </Box>
        </div>
      </div>
    </MuiThemeProvider>
  );
};

GithubRepositoriesForm.propTypes = {
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
    }).isRequired,
  }).isRequired,
};

export default GithubRepositoriesForm;
