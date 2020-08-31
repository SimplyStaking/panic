import { MissingArgument } from './utils/server/errors';

const express = require('express');
const path = require('path');
const responseUtils = require('./utils/server/response');

// TODO: Move logs to files

const app = express();
app.disable('x-powered-by');
// TODO: Need to check what these do
app.use(express.json()); // Recognize incoming data as json objects
app.use(express.static(path.join(__dirname, '../', 'build')));

// ---------------------------------------- Config get

app.get('/server/config', async (req, res) => {
  console.log('Received GET request for %s', req.url);
  const {
    configType, file, chainName, baseChain,
  } = req.query;

  if (!configType) {
    const err = new MissingArgument('configType');
    return res.status(err.code)
      .send(responseUtils.errorJson(err.message));
  }


  if (!authDetailsValid(req.session.username, req.session.password)) {
    return res.status(utils.ERR_STATUS)
      .send(utils.errorJson(msg.MSG_NOT_AUTHORIZED));
  }

  if (!file) {
    return res.status(utils.ERR_STATUS)
      .send(utils.errorJson(msg.MSG_MISSING_ARGUMENTS));
  }

  if (cfg.ALL_CONFIG_FILES.includes(file)) {
    try {
      const data = cfg.readConfig(file);
      return res.status(utils.SUCCESS_STATUS)
        .send(utils.resultJson(data));
    } catch (err) {
      if (err.code === 'ENOENT') {
        return res.status(utils.SUCCESS_STATUS)
          .send(utils.errorJson(msg.MSG_CONFIG_NOT_FOUND));
      }
      throw err;
    }
  }
  return res.status(utils.ERR_STATUS)
    .send(utils.errorJson(msg.MSG_CONFIG_UNRECOGNIZED));
});

// ---------------------------------------- Config post

app.post('/server/config', async (req, res) => {
  console.log('Received POST request for %s', req.url);
  const { file } = req.query;
  const { config } = req.body;

  if (!authDetailsValid(req.session.username, req.session.password)) {
    return res.status(utils.ERR_STATUS)
      .send(utils.errorJson(msg.MSG_NOT_AUTHORIZED));
  }

  if (!(file && config)) {
    return res.status(utils.ERR_STATUS)
      .send(utils.errorJson(msg.MSG_MISSING_ARGUMENTS));
  }

  if (cfg.ALL_CONFIG_FILES.includes(file)) {
    cfg.writeConfig(file, config);
    loadInfoFromUserConfigMain();
    return res.status(utils.SUCCESS_STATUS)
      .send(utils.resultJson(msg.MSG_CONFIG_SUBMITTED));
  }
  return res.status(utils.ERR_STATUS)
    .send(utils.errorJson(msg.MSG_CONFIG_UNRECOGNIZED));
});

// ---------------------------------------- Server default

app.get('/server/*', async (req, res) => {
  console.log('Received GET request for %s', req.url);
  res.status(utils.ERR_STATUS)
    .send(utils.errorJson(msg.MSG_INVALID_ENDPOINT));
});

app.post('/server/*', async (req, res) => {
  console.log('Received POST request for %s', req.url);
  res.status(utils.ERR_STATUS)
    .send(utils.errorJson(msg.MSG_INVALID_ENDPOINT));
});

// ---------------------------------------- PANIC UI

// TODO: Need to check if this has any effect
app.get('/*', (req, res) => {
  console.log('Received GET request for %s', req.url);
  res.sendFile(path.join(__dirname, 'build', 'index.html'));
});

// ---------------------------------------- Start listen

// TODO: Need to test if this works with docker
const port = process.env.INSTALLER_PORT || 8000;

app.listen(port, () => { console.log('Listening on %s', port); });
