const constants = require('./constants');

function InvalidConfigType() {
  this.message = 'The config type is invalid. It must either be \'channel\','
    + ' \'chain\' or \'other\'';
  this.code = constants.C_430;
}

function InvalidBaseChain() {
  this.message = 'The base chain is invalid. It must either be \'cosmos\' or '
    + '\'substrate\'';
  this.code = constants.C_431;
}

function MissingArguments(...args) {
  this.message = `Missing argument(s) '${args}'`;
  this.code = constants.C_432;
}

function ConfigUnrecognized(file) {
  this.message = `'${file}' does not belong to the inferred path.`;
  this.code = constants.C_433;
}

function ConfigNotFound(file) {
  this.message = `Cannot find '${file}' in the inferred path.`;
  this.code = constants.C_434;
}

function InvalidEndpoint(endpoint) {
  this.message = `'${endpoint}' is an invalid endpoint.`;
  this.code = constants.C_435;
}

function TwilioError(err) {
  this.message = `Twilio Error: ${err}`;
  this.code = constants.C_436;
}

function EmailError(err) {
  this.message = `Email Error: ${err}`;
  this.code = constants.C_437;
}

function PagerDutyError(err) {
  this.message = `PagerDuty Error: ${err}`;
  this.code = constants.C_438;
}

function OpsGenieError(err) {
  this.message = `OpsGenie Error: ${err}`;
  this.code = constants.C_439;
}

function MissingFile(filepath) {
  this.message = `Cannot find ${filepath}.`;
  this.code = constants.C_440;
}

function AuthenticationError(err) {
  this.message = `Authentication Error: ${err}.`;
  this.code = constants.C_441;
}

function MongoError(err) {
  this.message = `Mongo Error: ${err}`;
  this.code = constants.C_442;
}

function MissingInstallerCredentials(...args) {
  this.message = `Missing installer credential(s) '${args}' in .env. Server`
    + ' will stop.';
  this.code = constants.C_443;
}

function Unauthorized() {
  this.message = 'Not authorized to perform this operation.';
  this.code = constants.C_444;
}

function CouldNotFindRefreshTokenInDB() {
  this.message = 'Could not find refresh token in database.';
  this.code = constants.C_445;
}

function RecordAlreadyExists(keyValue) {
  this.message = `The record with key ${JSON.stringify(keyValue)} already `
    + ' exists in the database.';
  this.code = constants.C_446;
}

function UsernameAlreadyExists(username) {
  this.message = `Username '${username}' already exists.`;
  this.code = constants.C_447;
}

function CouldNotWriteConfig(err, config, path) {
  this.message = `Could not write config '${config}' to '${path}'. Error: `
    + `${err}`;
  this.code = constants.C_448;
}

function UsernameDoesNotExists(username) {
  this.message = `Username '${username}' does not exists.`;
  this.code = constants.C_449;
}

module.exports = {
  InvalidConfigType,
  InvalidBaseChain,
  MissingArguments,
  ConfigUnrecognized,
  ConfigNotFound,
  InvalidEndpoint,
  TwilioError,
  EmailError,
  PagerDutyError,
  OpsGenieError,
  MissingFile,
  AuthenticationError,
  MongoError,
  MissingInstallerCredentials,
  Unauthorized,
  CouldNotFindRefreshTokenInDB,
  RecordAlreadyExists,
  UsernameAlreadyExists,
  CouldNotWriteConfig,
  UsernameDoesNotExists,
};
