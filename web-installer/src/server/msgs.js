function ConfigSubmitted(config, path) {
  this.message = `${config} submitted in ${path}.`;
}

function TwilioCallSubmitted(phoneNumber) {
  this.message = `Twilio call to ${phoneNumber} submitted.`;
}

function EmailSubmitted(email) {
  this.message = `Email to ${email} submitted.`;
}

function TestAlertSubmitted() {
  this.message = 'Test alert submitted';
}

function TestEmail() {
  this.subject = 'Test Email from PANIC';
  this.text = 'Test Email from PANIC';
}

function TestAlert() {
  this.message = 'Test alert from PANIC';
}

function AuthenticationSuccessful() {
  this.message = 'Authentication Successful';
}

function AccountSavedSuccessfully() {
  this.message = 'Account saved successfully.';
}

function AccountRemovedSuccessfully() {
  this.message = 'Account removed successfully.';
}

function CollectionDropped(collection) {
  this.message = `Collection '${collection}' dropped from database.`;
}

function DirectoryNotCreated(directory) {
  this.message = `Directory '${directory}' was not created.`;
}

function MessagePong() {
  this.message = 'PONG';
}

function MessageNoConnection() {
  this.message = 'No connection.';
}

function ConnectionError() {
  this.message = 'Connection Error.';
}

function DeleteDirectory() {
  this.message = 'Deleted Directory.';
}

function MetricNotFound(metric, url) {
  this.message = `Metric: ${metric} not found at URL ${url}.`;
}

module.exports = {
  ConfigSubmitted,
  TwilioCallSubmitted,
  EmailSubmitted,
  TestEmail,
  TestAlert,
  TestAlertSubmitted,
  AuthenticationSuccessful,
  AccountSavedSuccessfully,
  AccountRemovedSuccessfully,
  CollectionDropped,
  DirectoryNotCreated,
  MessagePong,
  MessageNoConnection,
  ConnectionError,
  DeleteDirectory,
  MetricNotFound,
};
