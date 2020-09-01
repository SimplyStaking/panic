import React from 'react';
import {
  TextField, Button, Box, Checkbox, FormControlLabel, Typography, Switch,
} from '@material-ui/core';
import Grid from '@material-ui/core/Grid';
import PropTypes from 'prop-types';
import { withFormik } from 'formik';
import { connect } from 'react-redux';
import { makeStyles } from '@material-ui/core/styles';
import * as Yup from 'yup';
import { addTelegram } from '../../redux/actions/channelActions';

const useStyles = makeStyles(() => ({
  root: {
    display: 'flex',
    flexWrap: 'wrap',
    width: '100%',
  },
}));

const TelegramForm = (props) => {
  const classes = useStyles();

  const {
    errors,
    handleSubmit,
    values,
    handleChange,
    handleBlur,
  } = props;

  return (
    <div>
      <form onSubmit={handleSubmit} className={classes.root}>
        <Grid container spacing={3} justify="center" alignItems="center">
          <Grid item xs={2}>
            <Typography> Bot Name: </Typography>
          </Grid>
          <Grid item xs={10}>
            <TextField
              error={!errors.botName !== true}
              value={values.botName}
              type="text"
              name="botName"
              placeholder="telegram_chat_1"
              helperText={errors.botName ? 'Bot name is required!' : ''}
              onChange={handleChange}
              onBlur={handleBlur}
              fullWidth
            />
          </Grid>
          <Grid item xs={2}>
            <Typography> Bot Token: </Typography>
          </Grid>
          <Grid item xs={10}>
            <TextField
              value={values.botToken}
              type="text"
              name="botToken"
              placeholder="123456789:ABCDEF-1234abcd5678efgh12345_abc123"
              onChange={handleChange}
              onBlur={handleBlur}
              fullWidth
            />
          </Grid>
          <Grid item xs={2}>
            <Typography> Chat ID: </Typography>
          </Grid>
          <Grid item xs={10}>
            <TextField
              value={values.chatID}
              type="text"
              name="chatID"
              placeholder="-123456789"
              onChange={handleChange}
              onBlur={handleBlur}
              fullWidth
            />
          </Grid>
          <Grid item xs={2}>
            <Typography> Severities: </Typography>
          </Grid>
          <Grid item xs={10}>
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
          <Grid item xs={3}>
            <Typography> Telegram Commands: </Typography>
          </Grid>
          <Grid item xs={1}>
            <FormControlLabel
              control={(
                <Switch
                  checked={values.commands}
                  onChange={handleChange}
                  name="telegramCommands"
                  color="primary"
                />
              )}
            />
          </Grid>
          <Grid item xs={3}>
            <Typography> Telegram Alerts: </Typography>
          </Grid>
          <Grid item xs={1}>
            <FormControlLabel
              control={(
                <Switch
                  checked={values.alerts}
                  onChange={handleChange}
                  name="telegramAlerts"
                  color="primary"
                />
              )}
            />
          </Grid>
          <Grid item xs={4}>
            <Grid container direction="row" justify="flex-end" alignItems="center">
              <Box px={2}>
                <Button variant="outlined" size="large">
                  <Box px={2}>
                    Test
                  </Box>
                </Button>
                <Button variant="outlined" size="large" type="submit">
                  <Box px={2}>
                    Add
                  </Box>
                </Button>
              </Box>
            </Grid>
          </Grid>
        </Grid>
      </form>
    </div>
  );
};

const TelegramSchema = Yup.object().shape({
  botName: Yup.string()
    .required('Required'),
  botToken: Yup.string()
    .required('Required'),
  chatID: Yup.string()
    .required('Required'),
});

const Form = withFormik({

  mapPropsToValues: () => ({
    botName: '',
    botToken: '',
    chatID: '',
    info: false,
    warning: false,
    critical: false,
    error: false,
    alerts: true,
    commands: true,
  }),
  validationSchema: TelegramSchema,
  handleSubmit: (values, { props }) => {
    const { saveTelegramDetails } = props;
    const payload = {
      botName: values.botName,
      botToken: values.botToken,
      chatID: values.chatID,
      info: values.info,
      warning: values.warning,
      critical: values.critical,
      error: values.error,
      alerts: values.alerts,
      commands: values.commands,
    };
    saveTelegramDetails(payload);
  },
})(TelegramForm);

function mapDispatchToProps(dispatch) {
  return {
    saveTelegramDetails: (details) => dispatch(addTelegram(details)),
  };
}

TelegramForm.propTypes = {
  errors: PropTypes.shape({
    botName: PropTypes.string,
    botToken: PropTypes.string,
    chatID: PropTypes.string,
  }).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  values: PropTypes.shape({
    botName: PropTypes.string.isRequired,
    botToken: PropTypes.string.isRequired,
    chatID: PropTypes.string.isRequired,
    info: PropTypes.bool.isRequired,
    warning: PropTypes.bool.isRequired,
    critical: PropTypes.bool.isRequired,
    error: PropTypes.bool.isRequired,
    alerts: PropTypes.bool.isRequired,
    commands: PropTypes.bool.isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
  handleBlur: PropTypes.func.isRequired,
};

export default connect(null, mapDispatchToProps)(Form);
