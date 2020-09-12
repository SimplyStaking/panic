require('dotenv').config();
const express = require('express');
const path = require('path');
const twilio = require('twilio');
const nodemailer = require('nodemailer');
const opsgenie = require('opsgenie-sdk');
const PdClient = require('node-pagerduty');
const https = require('https');
const bodyParser = require('body-parser');
const mongoClient = require('mongodb').MongoClient;
const cookieParser = require('cookie-parser');
const jwt = require('jsonwebtoken');
const utils = require('./server/utils');
const errors = require('./server/errors');
const configs = require('./server/configs');
const msgs = require('./server/msgs');
const files = require('./server/files');
const mongo = require('./server/mongo');

// TODO: Continue with jwt
// TODO: Hash the password inside the database

// Read certificates. Note, the server will not start if the certificates are
// missing.
const httpsKey = files.readFile(
  path.join(__dirname, '../../', 'certificates', 'key.pem'),
);
const httpsCert = files.readFile(
  path.join(__dirname, '../../', 'certificates', 'cert.pem'),
);
const httpsOptions = {
  key: httpsKey,
  cert: httpsCert,
};

// Load installer authentication credentials and other info from .env
const installerCredentials = {
  INSTALLER_USERNAME: process.env.INSTALLER_USERNAME,
  INSTALLER_PASSWORD: process.env.INSTALLER_PASSWORD,
};
const dbname = process.env.DB_NAME;
const dbhost = '172.18.0.2:27017';
const authenticationCollection = 'installer_authentication';

const app = express();
app.disable('x-powered-by');
app.use(express.json()); // Recognize incoming data as json objects
// Render the build at the root url
app.use(express.static(path.join(__dirname, '../', 'build')));
app.use(bodyParser.json());
app.use(cookieParser());
const mongoDBUrl = `mongodb://${dbhost}/${dbname}`;

// Check which values are missing given an object, and return an array of
// missing values
function missingValues(values) {
  const missingValuesList = [];
  Object.keys(values).forEach((param) => {
    if (!values[param]) {
      missingValuesList.push(param);
    }
  });
  return missingValuesList;
}

function checkInstAuthCredentials() {
  // Check if installer credential are missing.
  const missingCredentialsList = missingValues(installerCredentials);

  // If any of the credentials is missing inform the user.
  if (missingCredentialsList.length !== 0) {
    throw new errors.MissingInstallerCredentials(missingCredentialsList);
  }
}

// This function loads the authentication details in .env to the database. This
// is needed to store the jwt token in case the server restarts (otherwise the
// user would need to login each time the server restarts)
async function loadAuthenticationToDB() {
  let client;
  let db;
  try {
    // connect
    client = await mongoClient.connect(mongoDBUrl, mongo.options);
    db = client.db(dbname);
    const collection = db.collection(authenticationCollection);
    const username = installerCredentials.INSTALLER_USERNAME;
    const password = installerCredentials.INSTALLER_PASSWORD;
    const authDoc = { username, password, refreshToken: '' };
    // Find authentication document
    const docs = await collection.find({ username }).toArray();
    if (!docs.length) {
      // If the credentials inside the .env are not found, empty the database so
      // that we always have one record (to prevent outside access), and insert
      // the credentials in the database.
      await collection.deleteMany({});
      await collection.insertOne(authDoc);
    } else {
      // Otherwise update the record with the latest password
      const newDoc = { $set: { password } };
      await collection.updateOne({ username }, newDoc);
    }
  } catch (err) {
    // If an error is raised throw a MongoError
    throw new errors.MongoError(err);
  } finally {
    // Check if an error was thrown after a connection was established. If this
    // is the case close the database connection to prevent leaks
    if (client && client.isConnected()) {
      await client.close();
    }
  }
}

// This endpoint saves the refresh token to the database
async function saveRefreshTokenToDB(username, password, refreshToken) {
  let client;
  let db;
  try {
    // connect
    client = await mongoClient.connect(mongoDBUrl, mongo.options);
    db = client.db(dbname);
    const collection = db.collection(authenticationCollection);
    const authDoc = { username, password, refreshToken };
    // Find authentication document
    const docs = await collection.find({ username }).toArray();
    // If we cannot find the authentication document, it must be that the
    // database was tampered with. Therefore save the .env credentials again
    // and update with the latest refresh token.
    if (!docs.length) {
      await loadAuthenticationToDB();
    }
    // Save the refresh token
    const newDoc = { $set: authDoc };
    await collection.updateOne({ username }, newDoc);
  } catch (err) {
    // If the error is already a mongo error no need to wrap it again as a mongo
    // error
    if (err.code === 442) {
      throw err;
    }
    throw new errors.MongoError(err);
  } finally {
    // Check if an error was thrown after a connection was established. If this
    // is the case close the database connection to prevent leaks
    if (client && client.isConnected()) {
      await client.close();
    }
  }
}

// ---------------------------------------- Configs

// This endpoint returns the configs. It infers the config path automatically
// from the parameters.
app.get('/server/config', async (req, res) => {
  console.log('Received GET request for %s', req.url);
  const {
    configType, fileName, chainName, baseChain,
  } = req.query;

  // Check if configType and fileName are missing, as these are independent of
  // other parameters
  const missingParamsList = missingValues({ configType, fileName });

  // If the config belongs to a chain, check if chainName and baseChain are
  // given. If not add them to the list of missing params.
  if (configType && configType.toLowerCase() === 'chain') {
    missingParamsList.push(...missingValues({ chainName, baseChain }));
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
  const missingParamsList = missingValues({ configType, fileName, config });

  // If the config belongs to a chain, check if chainName and baseChain are
  // given. If not add them to the list of missing params.
  if (configType && configType.toLowerCase() === 'chain') {
    missingParamsList.push(...missingValues({ chainName, baseChain }));
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
  const missingParamsList = missingValues({
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
  const missingParamsList = missingValues({ smtp, from, to });

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
  const missingParamsList = missingValues({ apiToken, integrationKey });

  // If some required parameters are missing inform the user.
  if (missingParamsList.length !== 0) {
    const err = new errors.MissingArguments(missingParamsList);
    res.status(err.code).send(utils.errorJson(err.message));
    return;
  }

  // Create PagerDuty client and test alert message
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
  console.log('Received POST request for %s', req.url);
  const { apiKey, eu } = req.body;

  // Check if apiKey is missing.
  const missingParamsList = missingValues({ apiKey });

  // If some required parameters are missing inform the user.
  if (missingParamsList.length !== 0) {
    const err = new errors.MissingArguments(missingParamsList);
    res.status(err.code).send(utils.errorJson(err.message));
    return;
  }

  // If the eu=true set the host to the opsgenie EU url otherwise the sdk will
  // run into an authentication error.
  const euString = String(eu);
  const host = utils.toBool(euString) ? 'https://api.eu.opsgenie.com'
    : 'https://api.opsgenie.com';

  // Create OpsGenie client and test alert message
  opsgenie.configure({ api_key: apiKey, host });
  const testAlert = new msgs.TestAlert();

  // Test alert object
  const alertObject = {
    message: testAlert.message,
    description: testAlert.message,
    priority: 'P5',
  };

  // Send test alert
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

// ---------------------------------------- Authentication

// Check if the inputted credentials are the one stored inside .env
function credentialsCorrect(username, password) {
  return username === installerCredentials.INSTALLER_USERNAME
    && password === installerCredentials.INSTALLER_PASSWORD;
}

// This endpoint attempts to login a user of the installer. The authentication
// credentials are the ones stored inside the .env file.
app.post('/server/login', async (req, res) => {
  console.log('Received POST request for %s', req.url);
  const { username, password } = req.body;

  // Check if username or password are missing.
  const missingParamsList = missingValues({ username, password });

  // If some required parameters are missing inform the user.
  if (missingParamsList.length !== 0) {
    const err = new errors.MissingArguments(missingParamsList);
    res.status(err.code).send(utils.errorJson(err.message));
    return;
  }

  // Check if the inputted credentials are correct.
  if (credentialsCorrect(username, password)) {
    // If the credentials are correct give the user a jwt token
    const payload = { username };
    const accessToken = jwt.sign(payload, process.env.ACCESS_TOKEN_SECRET, {
      algorithm: 'HS256',
      expiresIn: process.env.ACCESS_TOKEN_LIFE,
    });
    // This will be used to give access tokens
    const refreshToken = jwt.sign(payload, process.env.REFRESH_TOKEN_SECRET, {
      algorithm: 'HS256',
      expiresIn: process.env.REFRESH_TOKEN_LIFE,
    });
    // Inform the user that authentication was successful and wrap the token
    // inside a cookie for additional security
    const msg = new msgs.AuthenticationSuccessful();
    try {
      await saveRefreshTokenToDB(username, password, refreshToken);
      res.status(utils.SUCCESS_STATUS)
        .cookie('authCookie', accessToken, { secure: true, httpOnly: true })
        .send(utils.resultJson(msg.message));
    } catch (err) {
      // Inform the user of any error that occurs
      res.status(err.code).send(utils.errorJson(err.message));
    }
  } else {
    // If inputted credentials are incorrect inform the user
    const err = new errors.AuthenticationError('Incorrect Credentials');
    res.status(err.code).send(utils.errorJson(err.message));
  }
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

const port = process.env.INSTALLER_PORT || 8000;

(async () => {
  try {
    // Check that installer credentials are in the .env. If not inform the user
    // and terminate the server.
    checkInstAuthCredentials();
    // Load authentication details before listening for requests to avoid
    // unexpected behaviour.
    await loadAuthenticationToDB();
  } catch (err) {
    console.log(err);
    process.exit(0);
  }
  // Create Https server
  const server = https.createServer(httpsOptions, app);
  // Listen for requests
  server.listen(port, () => console.log('Listening on %s', port));
})().catch(err => console.log(err));
