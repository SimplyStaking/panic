const express = require('express');
const path = require('path');
const twilio = require('twilio');
const nodemailer = require('nodemailer');
const opsgenie = require('opsgenie-sdk');
const PdClient = require('node-pagerduty');
const utils = require('./server/utils');
const errors = require('./server/errors');
const configs = require('./server/configs');
const msgs = require('./server/msgs');

// TODO: Move logs to files

const app = express();
app.disable('x-powered-by');
app.use(express.json()); // Recognize incoming data as json objects
// Render the build at the root url
app.use(express.static(path.join(__dirname, '../', 'build')));

// ---------------------------------------- Configs

// Check which params are missing and return an array of missing params
function missingParams(params) {
  const missingParamsList = [];
  Object.keys(params).forEach((param) => {
    if (!params[param]) {
      missingParamsList.push(param);
    }
  });
  return missingParamsList;
}

// This endpoint returns the configs. It infers the config path automatically
// from the parameters.
app.get('/server/config', async (req, res) => {
  console.log('Received GET request for %s', req.url);
  const {
    configType, fileName, chainName, baseChain,
  } = req.query;

  // Check if configType and fileName are missing, as these are independent of
  // other parameters
  const missingParamsList = missingParams({ configType, fileName });

  // If the config belongs to a chain, check if chainName and baseChain are
  // given. If not add them to the list of missing params.
  if (configType && configType.toLowerCase() === 'chain') {
    missingParamsList.push(...missingParams({ chainName, baseChain }));
  }

  // If some required parameters are missing inform the user.
  if (missingParamsList.length !== 0) {
    const err = new errors.MissingArguments(missingParamsList);
    return res.status(err.code).send(utils.errorJson(err.message));
  }

  try {
    // If the file is expected in the inferred location get its path, read it
    // and send it to the client.
    if (configs.fileValid(configType, fileName)) {
      const configPath = configs.getConfigPath(
        configType, fileName, chainName, baseChain,
      );
      const data = configs.readConfig(configPath);
      return res.status(utils.SUCCESS_STATUS)
        .send(utils.resultJson(data));
    }
    // If the file is not expected in the inferred location inform the client.
    const err = new errors.ConfigUnrecognized(fileName);
    return res.status(err.code).send(utils.errorJson(err.message));
  } catch (err) {
    // If no valid path can be inferred from configType and baseChain return a
    // related error message
    if (err.code === 430 || err.code === 431) {
      return res.status(err.code).send(utils.errorJson(err.message));
    }
    // If the config cannot be found in the inferred location inform the client
    if (err.code === 'ENOENT') {
      const errNotFound = new errors.ConfigNotFound(fileName);
      return res.status(errNotFound.code)
        .send(utils.errorJson(errNotFound.message));
    }
    throw err;
  }
});

// This endpoint writes a config to the inferred path. The config path is
// inferred from the parameters.
app.post('/server/config', async (req, res) => {
  console.log('Received POST request for %s', req.url);
  const {
    configType, fileName, chainName, baseChain,
  } = req.query;
  const { config } = req.body;

  // Check if configType, fileName and config are missing as these are
  // independent of other parameters
  const missingParamsList = missingParams({ configType, fileName, config });

  // If the config belongs to a chain, check if chainName and baseChain are
  // given. If not add them to the list of missing params.
  if (configType && configType.toLowerCase() === 'chain') {
    missingParamsList.push(...missingParams({ chainName, baseChain }));
  }

  // If some required parameters are missing inform the user.
  if (missingParamsList.length !== 0) {
    const err = new errors.MissingArguments(missingParamsList);
    return res.status(err.code).send(utils.errorJson(err.message));
  }

  try {
    // If the file is expected in the inferred location get its path, write it
    // and inform the user if successful.
    if (configs.fileValid(configType, fileName)) {
      const configPath = configs.getConfigPath(
        configType, fileName, chainName, baseChain,
      );
      configs.writeConfig(configPath, config);
      const msg = new msgs.ConfigSubmitted(fileName, configPath);
      return res.status(utils.SUCCESS_STATUS)
        .send(utils.resultJson(msg.message));
    }
    // If the file is not expected in the inferred location inform the client.
    const err = new errors.ConfigUnrecognized(fileName);
    return res.status(err.code).send(utils.errorJson(err.message));
  } catch (err) {
    // If no valid path can be inferred from configType and baseChain return a
    // related error message
    if (err.code === 430 || err.code === 431) {
      return res.status(err.code).send(utils.errorJson(err.message));
    }
    throw err;
  }
});

// ---------------------------------------- Twilio

// This endpoint performs a twilio test call on the given phone number.
app.post('/server/twilio/test', async (req, res) => {
  console.log('Received POST request for %s', req.url);
  const {
    accountSid, authToken, twilioPhoneNumber, phoneNumberToDial,
  } = req.body;

  // Check if accountSid, authToken, twilioPhoneNumber and phoneNumberToDial
  // are missing.
  const missingParamsList = missingParams({
    accountSid, authToken, twilioPhoneNumber, phoneNumberToDial,
  });

  // If some required parameters are missing inform the user.
  if (missingParamsList.length !== 0) {
    const err = new errors.MissingArguments(missingParamsList);
    res.status(err.code).send(utils.errorJson(err.message));
    return;
  }

  // Create Twilio client
  let twilioClient;
  try {
    twilioClient = twilio(accountSid, authToken);
  } catch (err) {
    console.error(err);
    const error = new errors.TwilioError(err.message);
    res.status(error.code).send(utils.errorJson(error.message));
    return;
  }

  // Make call
  twilioClient.calls
    .create({
      twiml: '<Response><Reject /></Response>',
      to: phoneNumberToDial,
      from: twilioPhoneNumber,
    })
    .then(() => {
      const msg = new msgs.TwilioCallSubmitted(phoneNumberToDial);
      res.status(utils.SUCCESS_STATUS).send(utils.resultJson(msg.message));
    })
    .catch((err) => {
      console.error(err);
      const error = new errors.TwilioError(err.message);
      res.status(error.code).send(utils.errorJson(error.message));
    });
});

// ---------------------------------------- E-mail

// This endpoint sends a test e-mail to the address.
app.post('/server/email/test', async (req, res) => {
  console.log('Received POST request for %s', req.url);
  const {
    smtp, from, to, user, pass,
  } = req.body;

  // Check if smtp, from, to, user and pass are missing.
  const missingParamsList = missingParams({ smtp, from, to });

  // If some required parameters are missing inform the user.
  if (missingParamsList.length !== 0) {
    const err = new errors.MissingArguments(missingParamsList);
    res.status(err.code).send(utils.errorJson(err.message));
    return;
  }

  // Create mail transport (essentially an email client)
  const transport = nodemailer.createTransport({
    host: smtp,
    auth: (user && pass) ? {
      user,
      pass,
    } : undefined,
  });

  // If transporter valid, create and send test email
  transport.verify((err, _) => {
    if (err) {
      console.log(err);
      const error = new errors.EmailError(err.message);
      res.status(utils.ERR_STATUS).send(utils.errorJson(error.message));
      return;
    }

    const testEmail = new msgs.TestEmail();
    const message = {
      from,
      to,
      subject: testEmail.subject,
      text: testEmail.text,
    };

    // Send test email
    transport.sendMail(message, (err2, info) => {
      if (err2) {
        console.log(err2);
        const error = new errors.EmailError(err2.message);
        res.status(utils.ERR_STATUS).send(utils.errorJson(error.message));
        return;
      }
      console.debug(info);
      const msg = new msgs.EmailSubmitted(to);
      res.status(utils.SUCCESS_STATUS).send(utils.resultJson(msg.message));
    });
  });
});

// ---------------------------------------- PagerDuty

// This endpoint triggers an test alert event to the PagerDuty space.
app.post('/server/pagerduty/test', async (req, res) => {
  console.log('Received POST request for %s', req.url);
  const { apiToken, integrationKey } = req.body;

  // Check if apiToken and integrationKey are missing.
  const missingParamsList = missingParams({ apiToken, integrationKey });

  // If some required parameters are missing inform the user.
  if (missingParamsList.length !== 0) {
    const err = new errors.MissingArguments(missingParamsList);
    res.status(err.code).send(utils.errorJson(err.message));
    return;
  }

  // Create PagerDuty client and test alert
  const pdClient = new PdClient(apiToken);
  const testAlert = new msgs.TestAlert();

  // Send test alert event
  pdClient.events.sendEvent({
    routing_key: integrationKey,
    event_action: 'trigger',
    payload: {
      summary: testAlert.message,
      source: 'Test',
      severity: 'info',
    },
  }).then((response) => {
    console.log(response);
    const msg = new msgs.TestAlertSubmitted();
    res.status(utils.SUCCESS_STATUS).send(utils.resultJson(msg.message));
  }).catch((err) => {
    console.error(err);
    const error = new errors.PagerDutyError(err.message);
    res.status(error.code).send(utils.errorJson(error.message));
  });
});

// ---------------------------------------- OpsGenie

// This endpoint triggers a test alert event to the OpsGenie space.
app.post('/server/opsgenie/test', async (req, res) => {
  // TODO: error handling and different alert modifications in the struct
  console.log('Received POST request for %s', req.url);
  const { apiKey } = req.body;

  // Check if apiKey is missing.
  const missingParamsList = missingParams({ apiKey });

  // If some required parameters are missing inform the user.
  if (missingParamsList.length !== 0) {
    const err = new errors.MissingArguments(missingParamsList);
    res.status(err.code).send(utils.errorJson(err.message));
    return;
  }

  // Create OpsGenie client and test alert
  opsgenie.configure({ api_key: apiKey });
  const testAlert = new msgs.TestAlert();

  // Send test alert
  const alertObject = {
    message: testAlert.message,
  };

  opsgenie.alertV2.create(alertObject, (err, response) => {
    if (err) {
      console.error(err);
      const error = new errors.OpsGenieError(err.message);
      res.status(error.code).send(utils.errorJson(error.message));
    } else {
      console.log(response);
      const msg = new msgs.TestAlertSubmitted();
      res.status(utils.SUCCESS_STATUS).send(utils.resultJson(msg.message));
    }
  });
});

// ---------------------------------------- Server defaults

app.get('/server/*', async (req, res) => {
  console.log('Received GET request for %s', req.url);
  const err = new errors.InvalidEndpoint(req.url);
  res.status(err.code).send(utils.errorJson(err.message));
});

app.post('/server/*', async (req, res) => {
  console.log('Received POST request for %s', req.url);
  const err = new errors.InvalidEndpoint(req.url);
  res.status(err.code).send(utils.errorJson(err.message));
});

// ---------------------------------------- PANIC UI

// Return the build at the root URL
// TODO: Need to test if this is actually the case
app.get('/*', (req, res) => {
  console.log('Received GET request for %s', req.url);
  res.sendFile(path.join(__dirname, 'build', 'index.html'));
});

// ---------------------------------------- Start listen

// TODO: Need to test if this gets updated with docker
const port = process.env.INSTALLER_PORT || 8000;

app.listen(port, () => { console.log('Listening on %s', port); });
