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

module.exports = {
  InvalidConfigType,
  InvalidBaseChain,
  MissingArguments,
  ConfigUnrecognized,
  ConfigNotFound,
  InvalidEndpoint,
  TwilioError,
  EmailError,
};
