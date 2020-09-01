const express = require('express');
const path = require('path');
const response = require('./server/response');
const errors = require('./server/errors');
const configs = require('./server/configs');

// TODO: Move logs to files

const app = express();
app.disable('x-powered-by');
app.use(express.json()); // Recognize incoming data as json objects
// Render the build at the root url
app.use(express.static(path.join(__dirname, '../', 'build')));

// ---------------------------------------- Config get

app.get('/server/config', async (req, res) => {
  console.log('Received GET request for %s', req.url);
  const {
    configType, file, chainName, baseChain,
  } = req.query;

  // If configType is missing return an error message
  if (!configType) {
    const err = new errors.MissingArgument('configType');
    return res.status(err.code).send(response.errorJson(err.message));
  }

  // If file is missing return an error message
  if (!file) {
    const err = new errors.MissingArgument('file');
    return res.status(err.code).send(response.errorJson(err.message));
  }

  // If the config belongs to a chain, check if the chain name is given. If not
  // return an error message
  if (configType.toLowerCase() === 'chain' && !chainName) {
    const err = new errors.MissingArgument('chainName');
    return res.status(err.code).send(response.errorJson(err.message));
  }

  // If the config belongs to a chain, check if the base chain is given. If not
  // return an error message
  if (configType.toLowerCase() === 'chain' && !baseChain) {
    const err = new errors.MissingArgument('baseChain');
    return res.status(err.code).send(response.errorJson(err.message));
  }

  try {
    // If the file is expected in the inferred location get its path, read it
    // and send it to the client.
    if (configs.fileValid(configType, file)) {
      const configPath = configs.getConfigPath(
        configType, file, chainName, baseChain,
      );
      const data = configs.readConfig(configPath);
      return res.status(response.SUCCESS_STATUS)
        .send(response.resultJson(data));
    }
    // If the file is not expected in the inferred location inform the client.
    const err = new errors.ConfigUnrecognized(file);
    return res.status(err.code).send(response.errorJson(err.message));
  } catch (err) {
    // If no valid path can be inferred from configType and baseChain return a
    // related error message
    if (err.code === 430 || err.code === 431) {
      return res.status(err.code).send(response.errorJson(err.message));
    }
    // If the config cannot be found in the inferred location inform the client
    if (err.code === 'ENOENT') {
      const errNotFound = new errors.ConfigNotFound(file);
      return res.status(errNotFound.code)
        .send(response.errorJson(errNotFound.message));
    }
    throw err;
  }
});

// // ---------------------------------------- Config post
//
// app.post('/server/config', async (req, res) => {
//   console.log('Received POST request for %s', req.url);
//   const { file } = req.query;
//   const { config } = req.body;
//
//   if (!authDetailsValid(req.session.username, req.session.password)) {
//     return res.status(utils.ERR_STATUS)
//       .send(utils.errorJson(msg.MSG_NOT_AUTHORIZED));
//   }
//
//   if (!(file && config)) {
//     return res.status(utils.ERR_STATUS)
//       .send(utils.errorJson(msg.MSG_MISSING_ARGUMENTS));
//   }
//
//   if (cfg.ALL_CONFIG_FILES.includes(file)) {
//     cfg.writeConfig(file, config);
//     loadInfoFromUserConfigMain();
//     return res.status(utils.SUCCESS_STATUS)
//       .send(utils.resultJson(msg.MSG_CONFIG_SUBMITTED));
//   }
//   return res.status(utils.ERR_STATUS)
//     .send(utils.errorJson(msg.MSG_CONFIG_UNRECOGNIZED));
// });
//
// ---------------------------------------- Server default

app.get('/server/*', async (req, res) => {
  console.log('Received GET request for %s', req.url);
  const err = new errors.InvalidEndpoint(req.url);
  res.status(err.code).send(response.errorJson(err.message));
});

app.post('/server/*', async (req, res) => {
  console.log('Received POST request for %s', req.url);
  const err = new errors.InvalidEndpoint(req.url);
  res.status(err.code).send(response.errorJson(err.message));
});

// ---------------------------------------- PANIC UI

// Render the build at the root URL
// TODO: Need to test if this is actually the case
app.get('/*', (req, res) => {
  console.log('Received GET request for %s', req.url);
  res.sendFile(path.join(__dirname, 'build', 'index.html'));
});

// ---------------------------------------- Start listen

// TODO: Need to test if this gets updated with docker
const port = process.env.INSTALLER_PORT || 8000;

app.listen(port, () => { console.log('Listening on %s', port); });
