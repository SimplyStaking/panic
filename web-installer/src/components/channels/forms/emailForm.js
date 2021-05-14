import React from 'react';
import PropTypes from 'prop-types';
import {
  Box,
  Typography,
  FormControlLabel,
  Checkbox,
  Grid,
  Tooltip,
  InputAdornment,
} from '@material-ui/core';
import Button from 'components/material_ui/CustomButtons/Button';
import Divider from '@material-ui/core/Divider';
import InfoIcon from '@material-ui/icons/Info';
import { MuiThemeProvider } from '@material-ui/core/styles';
import { Autocomplete } from '@material-ui/lab';
import { SendTestEmailButton } from 'utils/buttons';
import { defaultTheme, theme } from 'components/theme/default';
import CssTextField from 'assets/jss/custom-jss/CssTextField';
import Data from 'data/channels';

const EmailForm = ({
  errors, values, handleSubmit, handleChange, setFieldValue,
}) => {
  const updateToEmails = (event, emailsTo) => {
    setFieldValue('emails_to', emailsTo);
  };

  return (
    <MuiThemeProvider theme={defaultTheme}>
      <div className="greyBackground">
        <Typography variant="subtitle1" gutterBottom>
          <Box m={2} pt={3} px={3}>
            <p
              style={{
                fontWeight: '350',
                fontSize: '1.2rem',
              }}
            >
              {Data.email.description}
            </p>
          </Box>
        </Typography>
        <Divider />
        <form onSubmit={handleSubmit} className="root">
          <Box m={2} p={3}>
            <Grid container spacing={1} justify="center" alignItems="center">
              <Grid item xs={12}>
                <CssTextField
                  id="channel-name-outlined-full-width"
                  error={errors.channel_name}
                  value={values.channel_name}
                  label="Configuration Name"
                  type="text"
                  style={{ margin: 8 }}
                  name="channel_name"
                  placeholder={Data.email.channelNamePlaceholder}
                  helperText={errors.channel_name ? errors.channel_name : ''}
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
                          <Tooltip title={Data.email.name} placement="left">
                            <InfoIcon />
                          </Tooltip>
                        </MuiThemeProvider>
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              <Grid item xs={12}>
                <CssTextField
                  id="smpt-outlined-full-width"
                  error={errors.smtp}
                  value={values.smtp}
                  label="SMTP"
                  type="text"
                  style={{ margin: 8 }}
                  name="smtp"
                  placeholder={Data.email.smtpPlaceholder}
                  helperText={errors.smtp ? errors.smtp : ''}
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
                          <Tooltip title={Data.email.smtp} placement="left">
                            <InfoIcon />
                          </Tooltip>
                        </MuiThemeProvider>
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              <Grid item xs={12}>
                <CssTextField
                  id="port-outlined-full-width"
                  error={errors.port}
                  value={values.port}
                  label="Port"
                  type="text"
                  style={{ margin: 8 }}
                  name="port"
                  placeholder={Data.email.portPlaceholder}
                  helperText={errors.port ? errors.port : ''}
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
                          <Tooltip title={Data.email.port} placement="left">
                            <InfoIcon />
                          </Tooltip>
                        </MuiThemeProvider>
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              <Grid item xs={12}>
                <CssTextField
                  id="email-from-outlined-full-width"
                  error={errors.email_from}
                  value={values.email_from}
                  label="Email From"
                  type="text"
                  style={{ margin: 8 }}
                  name="email_from"
                  placeholder={Data.email.emailFromPlaceHolder}
                  helperText={errors.email_from ? errors.email_from : ''}
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
                          <Tooltip title={Data.email.from} placement="left">
                            <InfoIcon />
                          </Tooltip>
                        </MuiThemeProvider>
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              <Grid item xs={12}>
                <Autocomplete
                  multiple
                  freeSolo
                  options={[]}
                  onChange={updateToEmails}
                  value={values.emails_to}
                  position="bottom"
                  renderInput={(params) => (
                    <CssTextField
                      // eslint-disable-next-line react/jsx-props-no-spreading
                      {...params}
                      id="emails-to-outlined-full-width"
                      error={errors.emails_to}
                      value={values.emails_to}
                      label="Emails To"
                      type="text"
                      style={{ margin: 8 }}
                      name="emails_to"
                      placeholder={Data.email.emailsToPlaceHolder}
                      helperText={errors.emails_to ? errors.emails_to : ''}
                      fullWidth
                      margin="normal"
                      InputLabelProps={{
                        shrink: true,
                      }}
                      variant="outlined"
                      autoComplete="off"
                    />
                  )}
                />
              </Grid>
              <Grid item xs={12}>
                <CssTextField
                  id="username-outlined-full-width"
                  value={values.username}
                  label="Username"
                  type="text"
                  style={{ margin: 8 }}
                  name="username"
                  placeholder={Data.email.usernamePlaceHolder}
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
                          <Tooltip title={Data.email.username} placement="left">
                            <InfoIcon />
                          </Tooltip>
                        </MuiThemeProvider>
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              <Grid item xs={12}>
                <CssTextField
                  id="password-outlined-full-width"
                  value={values.password}
                  label="Password"
                  type="password"
                  style={{ margin: 8 }}
                  name="password"
                  placeholder={Data.email.passwordPlaceHolder}
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
                          <Tooltip title={Data.email.password} placement="left">
                            <InfoIcon />
                          </Tooltip>
                        </MuiThemeProvider>
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              <Grid item xs={12} />
              <Grid container spacing={1} justify="center" alignItems="center">
                <Grid item xs={2}>
                  <Box pl={2}>
                    <Typography variant="subtitle1">
                      Severities
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={5}>
                  <FormControlLabel
                    control={(
                      <Checkbox
                        checked={values.info}
                        onChange={handleChange}
                        name="info"
                        color="primary"
                      />
                    )}
                    label="Info"
                    labelPlacement="start"
                  />
                  <FormControlLabel
                    control={(
                      <Checkbox
                        checked={values.warning}
                        onChange={handleChange}
                        name="warning"
                        color="primary"
                      />
                    )}
                    label="Warning"
                    labelPlacement="start"
                  />
                  <FormControlLabel
                    control={(
                      <Checkbox
                        checked={values.critical}
                        onChange={handleChange}
                        name="critical"
                        color="primary"
                      />
                    )}
                    label="Critical"
                    labelPlacement="start"
                  />
                  <FormControlLabel
                    control={(
                      <Checkbox
                        checked={values.error}
                        onChange={handleChange}
                        name="error"
                        color="primary"
                      />
                    )}
                    label="Error"
                    labelPlacement="start"
                  />
                </Grid>
                <Grid item xs={1}>
                  <Grid container justify="flex-end">
                    <Box pr={1}>
                      <MuiThemeProvider theme={theme}>
                        <Tooltip title={Data.email.severities} placement="left">
                          <InfoIcon />
                        </Tooltip>
                      </MuiThemeProvider>
                    </Box>
                  </Grid>
                </Grid>
                <Grid item xs={4}>
                  <Grid container direction="row" justify="flex-end" alignItems="center">
                    <Box pl={2}>
                      <SendTestEmailButton
                        disabled={Object.keys(errors).length !== 0}
                        to={values.emails_to}
                        from={values.email_from}
                        smtp={values.smtp}
                        user={values.username}
                        pass={values.password}
                        port={values.port}
                      />
                      <Button
                        color="primary"
                        size="md"
                        disabled={Object.keys(errors).length !== 0}
                        type="submit"
                      >
                        Add
                      </Button>
                    </Box>
                  </Grid>
                </Grid>
              </Grid>
            </Grid>
          </Box>
        </form>
      </div>
    </MuiThemeProvider>
  );
};

EmailForm.propTypes = {
  errors: PropTypes.shape({
    channel_name: PropTypes.string,
    smtp: PropTypes.string,
    email_from: PropTypes.string,
    emails_to: PropTypes.string,
    port: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    channel_name: PropTypes.string.isRequired,
    smtp: PropTypes.string.isRequired,
    port: PropTypes.number.isRequired,
    email_from: PropTypes.string.isRequired,
    emails_to: PropTypes.arrayOf(PropTypes.string.isRequired).isRequired,
    username: PropTypes.string.isRequired,
    password: PropTypes.string.isRequired,
    info: PropTypes.bool.isRequired,
    warning: PropTypes.bool.isRequired,
    critical: PropTypes.bool.isRequired,
    error: PropTypes.bool.isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
  setFieldValue: PropTypes.func.isRequired,
};

export default EmailForm;
