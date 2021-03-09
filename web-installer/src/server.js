require('dotenv').config();
const express = require('express');
const axios = require('axios');
const fs = require('fs');
const { resolve } = require('path');
const { readdir } = require('fs').promises;
const fsExtra = require('fs-extra');
const path = require('path');
const twilio = require('twilio');
const nodemailer = require('nodemailer');
const opsgenie = require('opsgenie-sdk');
const PdClient = require('node-pagerduty');
const https = require('https');
const bodyParser = require('body-parser');
const mongoClient = require('mongodb').MongoClient;
const cookieParser = require('cookie-parser');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const utils = require('./server/utils');
const errors = require('./server/errors');
const configs = require('./server/configs');
const msgs = require('./server/msgs');
const files = require('./server/files');
const mongo = require('./server/mongo');
const constants = require('./server/constants');

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
const dbip = process.env.DB_IP;
const dbport = process.env.DB_PORT;
const mongoDBUrl = `mongodb://${dbip}:${dbport}/${dbname}`;
const instAuthCollection = process.env.INSTALLER_AUTH_COLLECTION;
const accountsCollection = process.env.ACCOUNTS_COLLECTION;

// Store the amount of times a login attempt was made unsuccessfully
let loginAttempts = 0;
// Store when then next login attempt can be made
let lockedTime = 0;
// Store how long someone has to wait after 3 failed login attempts
const waitTime = 300000;

// Server configuration
const app = express();
app.disable('x-powered-by');
app.use(express.json());
app.use(express.static(path.join(__dirname, '../', 'build')));
app.use(bodyParser.json());
app.use(cookieParser());

// This function confirms that the authentication of the installer are in the
// .env file.
function checkInstAuthCredentials() {
  // Check if installer credentials are missing.
  const missingCredentialsList = utils.missingValues(installerCredentials);
  // If any of the credentials is missing stop the server with an exception.
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
    const collection = db.collection(instAuthCollection);
    const username = installerCredentials.INSTALLER_USERNAME;
    const hashedPass = bcrypt.hashSync(
      installerCredentials.INSTALLER_PASSWORD,
      10,
    );
    const password = installerCredentials.INSTALLER_PASSWORD;
    const authDoc = { username, password: hashedPass, refreshToken: '' };
    // Find authentication document
    const doc = await collection.findOne({ username });
    if (!doc) {
      // If the credentials inside the .env are not found insert the credentials
      // in the database.
      await collection.insertOne(authDoc);
      return;
    }
    // If the credentials are found and the password changed update the record.
    // We must also invalidate the refresh token so that eventually all logged
    // in users are logged out when the access token expires.
    if (!bcrypt.compareSync(password, doc.password)) {
      const newDoc = { $set: authDoc };
      await collection.updateOne({ username }, newDoc);
    }
  } catch (err) {
    // If an error is raised throw a MongoError
    throw new errors.MongoError(err.message);
  } finally {
    // Check if an error was thrown after a connection was established. If this
    // is the case close the database connection to prevent leaks
    if (client && client.isConnected()) {
      await client.close();
    }
  }
}

// This function retrieves the refresh token from the database
async function retrieveRefreshToken(username) {
  let client;
  let db;
  try {
    // connect
    client = await mongoClient.connect(mongoDBUrl, mongo.options);
    db = client.db(dbname);
    const collection = db.collection(instAuthCollection);
    // Find the authentication document
    const record = await collection.findOne({ username });
    if (!record) {
      // If the username is not found, return and empty string
      return '';
    }
    // Otherwise return the refresh token of the record.
    return record.refreshToken;
  } catch (err) {
    // If an error is raised throw a MongoError
    throw new errors.MongoError(err.message);
  } finally {
    // Check if an error was thrown after a connection was established. If this
    // is the case close the database connection to prevent leaks
    if (client && client.isConnected()) {
      await client.close();
    }
  }
}

// This function saves the refresh token to the database
async function saveRefreshTokenToDB(username, refreshToken) {
  let client;
  let db;
  try {
    // connect
    client = await mongoClient.connect(mongoDBUrl, mongo.options);
    db = client.db(dbname);
    const collection = db.collection(instAuthCollection);
    // Find authentication document
    const doc = await collection.findOne({ username });
    // If we cannot find the authentication document, it must be that the
    // database was tampered with. Therefore save the .env credentials again
    // and update with the latest refresh token.
    if (!doc) {
      await loadAuthenticationToDB();
    }
    // Save the refresh token
    const newDoc = { $set: { refreshToken } };
    await collection.updateOne({ username }, newDoc);
  } catch (err) {
    // If the error is already a mongo error no need to wrap it again as a mongo
    // error
    if (err.code === constants.C_442) {
      throw err;
    }
    throw new errors.MongoError(err.message);
  } finally {
    // Check if an error was thrown after a connection was established. If this
    // is the case close the database connection to prevent leaks
    if (client && client.isConnected()) {
      await client.close();
    }
  }
}

// ---------------------------------------- Authentication

// Check if the inputted credentials are the one stored inside .env
function credentialsCorrect(username, password) {
  return (
    username === installerCredentials.INSTALLER_USERNAME
    && password === installerCredentials.INSTALLER_PASSWORD
  );
}

function verify(req, res, next) {
  // Extract the authentication cookie
  const accessToken = req.cookies.authCookie;
  // If authCookie does not exist, the user did not login therefore send an
  // unauthorized error
  if (!accessToken) {
    const err = new errors.Unauthorized();
    res.status(err.code).send(utils.errorJson(err.message));
    return;
  }
  try {
    // Use the jwt.verify method to verify the access token. It throws an
    // error if the token has expired or has a invalid signature
    jwt.verify(accessToken, process.env.ACCESS_TOKEN_SECRET);
    next();
  } catch (err) {
    console.log(err);
    // If an error occurs send an unauthorized error
    const error = new errors.Unauthorized();
    res.status(error.code).send(utils.errorJson(error.message));
  }
}

// This endpoint attempts to login a user of the installer. The authentication
// credentials are the ones stored inside the .env file.
app.post('/server/login', async (req, res) => {
  console.log('Received POST request for %s', req.url);
  const { username, password } = req.body;

  // Check if username or password are missing.
  const missingParamsList = utils.missingValues({ username, password });

  // If some required parameters are missing inform the user.
  if (missingParamsList.length !== 0) {
    const err = new errors.MissingArguments(missingParamsList);
    res.status(err.code).send(utils.errorJson(err.message));
    return;
  }
  let currentTime = new Date().getTime();
  // Check if the checking of credentials is locked
  if (lockedTime < currentTime) {
    // Check if the inputted credentials are correct.
    if (credentialsCorrect(username, password)) {
      // If the credentials are correct give the user a jwt token
      const payload = { username };
      const accessToken = jwt.sign(payload, process.env.ACCESS_TOKEN_SECRET, {
        algorithm: 'HS256',
        expiresIn: parseInt(process.env.ACCESS_TOKEN_LIFE, 10),
      });
      // This will be used to give access tokens
      const refreshToken = jwt.sign(payload, process.env.REFRESH_TOKEN_SECRET, {
        algorithm: 'HS256',
        expiresIn: parseInt(process.env.REFRESH_TOKEN_LIFE, 10),
      });
      // Inform the user that authentication was successful and wrap the token
      // inside a cookie for additional security
      const msg = new msgs.AuthenticationSuccessful();
      try {
        await saveRefreshTokenToDB(username, refreshToken);
        res
          .status(utils.SUCCESS_STATUS)
          .cookie('authCookie', accessToken, {
            secure: true,
            httpOnly: true,
            sameSite: true,
            maxAge: parseInt(process.env.ACCESS_TOKEN_LIFE, 10) * 1000,
          })
          .send(utils.resultJson(msg.message));
      } catch (err) {
        // Inform the user of any error that occurs
        res.status(err.code).send(utils.errorJson(err.message));
      }
    } else {
      // Increment the login attempts
      loginAttempts = loginAttempts + 1;
      if (loginAttempts === 3) {
        // Set the locked time
        lockedTime = currentTime + waitTime;
        // Reset the login attempts
        loginAttempts = 0;
        const err = new errors.AuthenticationError(`Incorrect Credentials,
            ${0} remaining login attempts, login is locked for 5 minutes`);
        console.log(err);
        res.status(err.code).send(utils.errorJson(err.message));
      }else {
        // If inputted credentials are incorrect inform the user
        let remainingAttempts = 3 - loginAttempts;
        const err = new errors.AuthenticationError(`Incorrect Credentials,
          ${remainingAttempts} remaining login attempts before it's
          locked for 5 minutes`);
        console.log(err);
        res.status(err.code).send(utils.errorJson(err.message));
      }
    }
  }else {
    // If the login is locked for a certain amount of time inform the user
    const err = new errors.LoginLockedError((lockedTime - currentTime)/1000);
    console.log(err);
    res.status(err.code).send(utils.errorJson(err.message));
  }
});

// This endpoint returns a new access token using the stored refresh token if
// the current access token has a valid signature.
app.post('/server/refresh', async (req, res) => {
  console.log('Received POST request for %s', req.url);
  // Extract the authentication cookie
  const accessToken = req.cookies.authCookie;
  // If it does not exist, the user did not login therefore send an unauthorized
  // error
  if (!accessToken) {
    const err = new errors.Unauthorized();
    res.status(err.code).send(utils.errorJson(err.message));
    return;
  }

  let payload;
  try {
    // Use the jwt.verify method to verify that the access token has a valid
    // signature and not expired, it throws an error otherwise. This is done
    // so that no one can issue new tokens with stolen.
    payload = jwt.verify(accessToken, process.env.ACCESS_TOKEN_SECRET);
  } catch (err) {
    console.log(err);
    // If an error occurs send an unauthorized error
    const error = new errors.Unauthorized();
    res.status(error.code).send(utils.errorJson(error.message));
    return;
  }

  let refreshToken;
  try {
    // Get the refresh token from the database
    refreshToken = await retrieveRefreshToken(payload.username);
    // If the refresh token could not be found in the database inform the user.
    if (refreshToken === '') {
      throw new errors.CouldNotFindRefreshTokenInDB();
    }
  } catch (err) {
    // Inform the user of any error that occurs when retrieving the token
    console.log(err);
    res.status(err.code).send(utils.errorJson(err.message));
    return;
  }

  // Verify the refresh token. If the token expired or is invalid send an
  // unauthorized access message to the user.
  try {
    jwt.verify(refreshToken, process.env.REFRESH_TOKEN_SECRET);
  } catch (err) {
    console.log(err);
    // If an error occurs send an unauthorized error
    const error = new errors.Unauthorized();
    res.status(error.code).send(utils.errorJson(error.message));
    return;
  }

  try {
    // Wrap the new token inside a cookie for additional security and inform the
    // user that he has been authenticated again
    const msg = new msgs.AuthenticationSuccessful();
    const newPayload = { username: payload.username }; // Must be overwritten
    const newAccessToken = jwt.sign(
      newPayload,
      process.env.ACCESS_TOKEN_SECRET,
      {
        algorithm: 'HS256',
        expiresIn: parseInt(process.env.ACCESS_TOKEN_LIFE, 10),
      },
    );
    res
      .status(utils.SUCCESS_STATUS)
      .cookie('authCookie', newAccessToken, {
        secure: true,
        httpOnly: true,
        sameSite: true,
        maxAge: parseInt(process.env.ACCESS_TOKEN_LIFE, 10) * 1000,
      })
      .send(utils.resultJson(msg.message));
  } catch (err) {
    // Inform the user of any error that occurs
    console.log(err);
    res.status(err.code).send(utils.errorJson(err.message));
  }
});

// ---------------------------------------- Account

// This endpoint saves an account inside the database
app.post('/server/account/save', verify, async (req, res) => {
  console.log('Received POST request for %s', req.url);
  const { username, password } = req.body;
  // Check if username and password are missing
  const missingParamsList = utils.missingValues({ username, password });
  // If some required parameters are missing inform the user.
  if (missingParamsList.length !== 0) {
    const err = new errors.MissingArguments(missingParamsList);
    res.status(err.code).send(utils.errorJson(err.message));
    return;
  }
  // Hash the password to be stored inside the database
  const hashedPass = bcrypt.hashSync(password, 10);
  const record = { username, password: hashedPass, refreshToken: '' };

  try {
    // Save the record to the database and inform the user if successful
    await mongo.saveToDatabase(mongoDBUrl, dbname, record, accountsCollection, {
      username,
    });
    const msg = new msgs.AccountSavedSuccessfully();
    res.status(utils.SUCCESS_STATUS).send(utils.resultJson(msg.message));
  } catch (err) {
    // If the record is already present in the database return a username
    // already exists error so that the error is more meaningful. Otherwise
    // return whatever error is thrown.
    if (err.code === constants.C_446) {
      const error = new errors.UsernameAlreadyExists(username);
      console.log(error);
      res.status(error.code).send(utils.errorJson(error.message));
      return;
    }
    console.log(err);
    res.status(err.code).send(utils.errorJson(err.message));
  }
});

// This should remove an account by username from the database
app.post('/server/account/delete', verify, async (req, res) => {
  console.log('Received POST request for %s', req.url);
  const { username } = req.body;
  // Check if username is missing
  const missingParamsList = utils.missingValues({ username });
  // If some required parameters are missing inform the user.
  if (missingParamsList.length !== 0) {
    const err = new errors.MissingArguments(missingParamsList);
    res.status(err.code).send(utils.errorJson(err.message));
    return;
  }

  try {
    // Remove an account from the collection
    await mongo.removeFromCollection(mongoDBUrl, dbname, accountsCollection, {
      username,
    });
    const msg = new msgs.AccountRemovedSuccessfully();
    res.status(utils.SUCCESS_STATUS).send(utils.resultJson(msg.message));
  } catch (err) {
    // If the record is already present in the database return a username
    // already exists error so that the error is more meaningful. Otherwise
    // return whatever error is thrown.
    if (err.code === constants.C_446) {
      const error = new errors.UsernameDoesNotExists(username);
      console.log(error);
      res.status(error.code).send(utils.errorJson(error.message));
      return;
    }
    console.log(err);
    res.status(err.code).send(utils.errorJson(err.message));
  }
});

// This endpoint checks whether an account already exists with the given
// username
app.post('/server/account/exists', verify, async (req, res) => {
  console.log('Received POST request for %s', req.url);
  const { username } = req.body;
  // Check if username is missing
  const missingParamsList = utils.missingValues({ username });
  // If some required parameters are missing inform the user.
  if (missingParamsList.length !== 0) {
    const err = new errors.MissingArguments(missingParamsList);
    res.status(err.code).send(utils.errorJson(err.message));
    return;
  }
  try {
    // Check if the username already exists and inform the user about the result
    const result = await mongo.recordExists(
      mongoDBUrl,
      dbname,
      accountsCollection,
      { username },
    );
    res.status(utils.SUCCESS_STATUS).send(utils.resultJson(result));
  } catch (err) {
    // Inform the user of any errors.
    console.log(err);
    res.status(err.code).send(utils.errorJson(err.message));
  }
});

// This endpoint returns all the usernames of the accounts saved
app.get('/server/account/usernames', verify, async (req, res) => {
  console.log('Received GET request for %s', req.url);
  try {
    const result = await mongo.getRecords(
      mongoDBUrl,
      dbname,
      accountsCollection,
    );
    res.status(utils.SUCCESS_STATUS).send(utils.resultJson(result));
  } catch (err) {
    // Inform the user of any errors.
    console.log(err);
    res.status(err.code).send(utils.errorJson(err.message));
  }
});

// ---------------------------------------- MongoDB

// This endpoint saves an account inside the database
app.post('/server/database/drop', verify, async (req, res) => {
  console.log('Received POST request for %s', req.url);
  const { collection } = req.body;

  // Check if the collection parameter is missing
  const missingParamsList = utils.missingValues({ collection });
  // If some required parameters are missing inform the user.
  if (missingParamsList.length !== 0) {
    const err = new errors.MissingArguments(missingParamsList);
    res.status(err.code).send(utils.errorJson(err.message));
    return;
  }
  try {
    // Drop the collection from the database and inform the user if successful
    await mongo.dropCollection(mongoDBUrl, dbname, collection);
    const msg = new msgs.CollectionDropped(collection);
    res.status(utils.SUCCESS_STATUS).send(utils.resultJson(msg.message));
  } catch (err) {
    // Give an error message to the user if the endpoint runs into an error
    console.log(err);
    res.status(err.code).send(utils.errorJson(err.message));
  }
});

// ---------------------------------------- Configs

// This endpoint is used to a list of paths inside the configuration
// folder
app.get('/server/paths', verify, async (req, res) => {
  console.log('Received GET request for %s', req.url);
  const configPath = path.join(__dirname, '../../', 'config');
  try {
    const foundFiles = files
      .getFiles(configPath)
      .then((returnedFiles) => {
        const processedPaths = [];
        for (let i = 0; i < returnedFiles.length; i += 1) {
          const newPath = returnedFiles[i].replace(configPath, '');
          processedPaths.push(newPath);
        }
        return processedPaths;
      })
      .catch((e) => console.error(e));
    return res
      .status(utils.SUCCESS_STATUS)
      .send(utils.resultJson(await foundFiles));
  } catch (err) {
    console.log(err);
    // Inform the user about the error.
    return res.status(err.code).send(utils.errorJson(err.message));
  }
});

// This endpoint returns the configs. It infers the config path automatically
// from the parameters.
app.get('/server/config', verify, async (req, res) => {
  console.log('Received GET request for %s', req.url);
  const {
    configType, fileName, chainName, baseChain,
  } = req.query;

  // Check if configType and fileName are missing, as these are independent of
  // other parameters
  const missingParamsList = utils.missingValues({ configType, fileName });

  // If the config belongs to a chain, check if chainName and baseChain are
  // given. If not add them to the list of missing params.
  if (configType && configType.toLowerCase() === 'chain') {
    missingParamsList.push(...utils.missingValues({ chainName, baseChain }));
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
        configType,
        fileName,
        chainName,
        baseChain,
      );
      const data = configs.readConfig(configPath);
      return res.status(utils.SUCCESS_STATUS).send(utils.resultJson(data));
    }
    // If the file is not expected in the inferred location inform the client.
    const err = new errors.ConfigUnrecognized(fileName);
    return res.status(err.code).send(utils.errorJson(err.message));
  } catch (err) {
    // If the config cannot be found in the inferred location inform the client
    if (err.code === 'ENOENT') {
      const errNotFound = new errors.ConfigNotFound(fileName);
      console.log(err);
      return res
        .status(errNotFound.code)
        .send(utils.errorJson(errNotFound.message));
    }
    console.log(err);
    // Otherwise inform the user about the error.
    return res.status(err.code).send(utils.errorJson(err.message));
  }
});

// Endpoint to delete all directories so they can be re-written
app.post('/server/config/delete', verify, async (req, res) => {
  console.log('Received POST request for %s', req.url);

  try {
    const configPath = path.join(__dirname, '../../', 'config');
    const gitKeep = path.join(configPath, '/', '.gitkeep')
    fsExtra.emptyDirSync(configPath);
    try {
      await fs.openSync(gitKeep, 'w');
    } catch (error) {
      console.log(error);
    }
    const msg = new msgs.DeleteDirectory();
    return res.status(utils.SUCCESS_STATUS).send(utils.resultJson(msg.message));
  } catch (err) {
    console.log(err);
    // If error inform the user
    return res.status(err.code).send(utils.errorJson(err.message));
  }
});

// This endpoint writes a config to the inferred path. The config path is
// inferred from the parameters.
app.post('/server/config', verify, async (req, res) => {
  console.log('Received POST request for %s', req.url);
  const {
    configType, fileName, chainName, baseChain,
  } = req.query;
  const { config } = req.body;
  // Check if configType, fileName and config are missing as these are
  // independent of other parameters
  const missingParamsList = utils.missingValues({
    configType,
    fileName,
    config,
  });

  // If the config belongs to a chain, check if chainName and baseChain are
  // given. If not add them to the list of missing params.
  if (configType && configType.toLowerCase() === 'chain') {
    missingParamsList.push(...utils.missingValues({ chainName, baseChain }));
  }

  // If some required parameters are missing inform the user.
  if (missingParamsList.length !== 0) {
    const err = new errors.MissingArguments(missingParamsList);
    console.log(err);
    return res.status(err.code).send(utils.errorJson(err.message));
  }

  try {
    // If the file is expected in the inferred location get its path, write it
    // and inform the user if successful.
    if (configs.fileValid(configType, fileName)) {
      const configPath = configs.getConfigPath(
        configType,
        fileName,
        chainName,
        baseChain,
      );
      configs.writeConfig(configPath, config);
      const msg = new msgs.ConfigSubmitted(fileName, configPath);
      return res
        .status(utils.SUCCESS_STATUS)
        .send(utils.resultJson(msg.message));
    }
    // If the file is not expected in the inferred location inform the client.
    const err = new errors.ConfigUnrecognized(fileName);
    return res.status(err.code).send(utils.errorJson(err.message));
  } catch (err) {
    console.log(err);
    // If error inform the user
    return res.status(err.code).send(utils.errorJson(err.message));
  }
});

// ---------------------------------------- Twilio

// This endpoint performs a twilio test call on the given phone number.
app.post('/server/twilio/test', verify, async (req, res) => {
  console.log('Received POST request for %s', req.url);
  const {
    accountSid,
    authToken,
    twilioPhoneNumber,
    phoneNumberToDial,
  } = req.body;

  // Check if accountSid, authToken, twilioPhoneNumber and phoneNumberToDial
  // are missing.
  const missingParamsList = utils.missingValues({
    accountSid,
    authToken,
    twilioPhoneNumber,
    phoneNumberToDial,
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
app.post('/server/email/test', verify, async (req, res) => {
  console.log('Received POST request for %s', req.url);
  const {
    smtp, from, to, user, pass, port,
  } = req.body;

  // Check if smtp, from, to, user and pass are missing.
  const missingParamsList = utils.missingValues({ smtp, from, to });

  // If some required parameters are missing inform the user.
  if (missingParamsList.length !== 0) {
    const err = new errors.MissingArguments(missingParamsList);
    res.status(err.code).send(utils.errorJson(err.message));
    return;
  }

  // Create mail transport (essentially an email client)
  const transport = nodemailer.createTransport({
    host: smtp,
    port,
    auth:
      user && pass
        ? {
          user,
          pass,
        }
        : undefined,
  });

  // If transporter valid, create and send test email
  transport.verify((err, _) => {
    if (err) {
      console.log(err);
      const error = new errors.EmailError(err.message);
      res.status(error.code).send(utils.errorJson(error.message));
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
        res.status(error.code).send(utils.errorJson(error.message));
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
app.post('/server/pagerduty/test', verify, async (req, res) => {
  console.log('Received POST request for %s', req.url);
  const { apiToken, integrationKey } = req.body;

  // Check if apiToken and integrationKey are missing.
  const missingParamsList = utils.missingValues({ apiToken, integrationKey });

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
  pdClient.events
    .sendEvent({
      routing_key: integrationKey,
      event_action: 'trigger',
      payload: {
        summary: testAlert.message,
        source: 'Test',
        severity: 'info',
      },
    })
    .then((response) => {
      console.log(response);
      const msg = new msgs.TestAlertSubmitted();
      res.status(utils.SUCCESS_STATUS).send(utils.resultJson(msg.message));
    })
    .catch((err) => {
      console.error(err);
      const error = new errors.PagerDutyError(err.message);
      res.status(error.code).send(utils.errorJson(error.message));
    });
});

// ---------------------------------------- OpsGenie

// This endpoint triggers a test alert event to the OpsGenie space.
app.post('/server/opsgenie/test', verify, async (req, res) => {
  console.log('Received POST request for %s', req.url);
  const { apiKey, eu } = req.body;
  // Check if apiKey is missing.
  const missingParamsList = utils.missingValues({ apiKey });

  // If some required parameters are missing inform the user.
  if (missingParamsList.length !== 0) {
    const err = new errors.MissingArguments(missingParamsList);
    res.status(err.code).send(utils.errorJson(err.message));
    return;
  }

  // If the eu=true set the host to the opsgenie EU url otherwise the sdk will
  // run into an authentication error.
  const euString = String(eu);
  const host = utils.toBool(euString)
    ? 'https://api.eu.opsgenie.com'
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

// ---------------------------------------- Cosmos

app.post('/server/cosmos/tendermint', async (req, res) => {
  console.log('Received POST request for %s', req.url);
  const { tendermintRpcUrl } = req.body;

  // Check if tendermintRpcUrl is missing.
  const missingParamsList = utils.missingValues({ tendermintRpcUrl });

  // If some required parameters are missing inform the user.
  if (missingParamsList.length !== 0) {
    const err = new errors.MissingArguments(missingParamsList);
    res.status(err.code).send(utils.errorJson(err.message));
    return;
  }

  const url = `${tendermintRpcUrl}/health?`;

  axios
    .get(url, { params: {} })
    .then((_) => {
      const msg = new msgs.MessagePong();
      res.status(utils.SUCCESS_STATUS).send(utils.resultJson(msg.message));
    })
    .catch((err) => {
      console.error(err);
      if (err.code === 'ECONNREFUSED') {
        const msg = new msgs.MessageNoConnection();
        res.status(utils.ERR_STATUS).send(utils.errorJson(msg.message));
      } else {
        const msg = new msgs.ConnectionError();
        // Connection made but error occurred (typically means node is missing)
        res.status(utils.ERR_STATUS).send(utils.errorJson(msg.message));
      }
    });
});

app.post('/server/cosmos/prometheus', async (req, res) => {
  console.log('Received POST request for %s', req.url);
  const { prometheusUrl } = req.body;

  // Check if prometheusUrl is missing.
  const missingParamsList = utils.missingValues({ prometheusUrl });

  // If some required parameters are missing inform the user.
  if (missingParamsList.length !== 0) {
    const err = new errors.MissingArguments(missingParamsList);
    res.status(err.code).send(utils.errorJson(err.message));
    return;
  }

  const url = `${prometheusUrl}`;

  axios
    .get(url, { params: {} })
    .then((_) => {
      const msg = new msgs.MessagePong();
      res.status(utils.SUCCESS_STATUS).send(utils.resultJson(msg.message));
    })
    .catch((err) => {
      console.error(err);
      if (err.code === 'ECONNREFUSED') {
        const msg = new msgs.MessageNoConnection();
        res.status(utils.ERR_STATUS).send(utils.errorJson(msg.message));
      } else {
        const msg = new msgs.ConnectionError();
        // Connection made but error occurred (typically means node is missing
        // or prometheus is not enabled)
        res.status(utils.ERR_STATUS).send(utils.errorJson(msg.message));
      }
    });
});

// ---------------------------------------- System (Node Exporter)

app.post('/server/system/exporter', async (req, res) => {
  console.log('Received POST request for %s', req.url);
  const { exporterUrl } = req.body;

  // Check if exporterUrl is missing.
  const missingParamsList = utils.missingValues({ exporterUrl });

  // If some required parameters are missing inform the user.
  if (missingParamsList.length !== 0) {
    const err = new errors.MissingArguments(missingParamsList);
    res.status(err.code).send(utils.errorJson(err.message));
    return;
  }

  axios
    .get(exporterUrl, { params: {} })
    .then((_) => {
      const msg = new msgs.MessagePong();
      res.status(utils.SUCCESS_STATUS).send(utils.resultJson(msg.message));
    })
    .catch((err) => {
      console.error(err);
      if (err.code === 'ECONNREFUSED') {
        const msg = new msgs.MessageNoConnection();
        res.status(utils.ERR_STATUS).send(utils.errorJson(msg.message));
      } else {
        const msg = new msgs.ConnectionError();
        // Connection made but error occurred node exporter is not installed
        res.status(utils.ERR_STATUS).send(utils.errorJson(msg.message));
      }
    });
});

// ---------------------------------------- Server defaults

app.get('/server/*', verify, async (req, res) => {
  console.log('Received GET request for %s', req.url);
  const err = new errors.InvalidEndpoint(req.url);
  res.status(err.code).send(utils.errorJson(err.message));
});

app.post('/server/*', verify, async (req, res) => {
  console.log('Received POST request for %s', req.url);
  const err = new errors.InvalidEndpoint(req.url);
  res.status(err.code).send(utils.errorJson(err.message));
});

// ---------------------------------------- PANIC UI

// Return the build at the root URL
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
})().catch((err) => console.log(err));
