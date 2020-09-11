// TODO: Pass more arguments to possibly make the errors more meaningful

function InvalidConfigType() {
  this.message = 'The config type is invalid. It must either be \'channel\','
    + ' \'chain\', \'ui\' or \'other\'';
  this.code = 430;
}

function InvalidBaseChain() {
  this.message = 'The base chain is invalid. It must either be \'cosmos\' or '
    + '\'substrate\'';
  this.code = 431;
}

function MissingArguments(...args) {
  this.message = `Missing argument(s) '${args}'`;
  this.code = 432;
}

function ConfigUnrecognized(file) {
  this.message = `'${file}' does not belong to the inferred path.`;
  this.code = 433;
}

function ConfigNotFound(file) {
  this.message = `Cannot find '${file}' in the inferred path.`;
  this.code = 434;
}

function InvalidEndpoint(endpoint) {
  this.message = `'${endpoint}' is an invalid endpoint.`;
  this.code = 435;
}

function TwilioError(err) {
  this.message = `Twilio Error: ${err}`;
  this.code = 436;
}

function EmailError(err) {
  this.message = `Email Error: ${err}`;
  this.code = 437;
}

function PagerDutyError(err) {
  this.message = `PagerDuty Error: ${err}`;
  this.code = 438;
}

function OpsGenieError(err) {
  this.message = `OpsGenie Error: ${err}`;
  this.code = 439;
}

function MissingFile(filepath) {
  this.message = `Cannot find ${filepath}.`;
  this.code = 440;
}

function AuthenticationError(err) {
  this.message = `Authentication Error: ${err}.`;
  this.code = 441;
}

function MongoError(err) {
  this.message = `Mongo Error: ${err}`;
  this.code = 442;
}

function MissingInstallerCredentials(...args) {
  this.message = `Missing installer credential(s) '${args}' in .env. Server`
    + ' will stop.';
  this.code = 443;
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
};
