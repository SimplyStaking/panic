const express = require('express');
const path = require('path');
const twilio = require('twilio');
const nodemailer = require('nodemailer');
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

app.post('/server/twilio_test_call', async (req, res) => {
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

app.post('/server/test_email', async (req, res) => {
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
