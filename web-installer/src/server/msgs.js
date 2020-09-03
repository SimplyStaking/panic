function ConfigSubmitted(config, path) {
  this.message = `${config} submitted in ${path}.`;
}

function TwilioCallSubmitted(phoneNumber) {
  this.message = `Twilio call to ${phoneNumber} submitted.`;
}

module.exports = {
  ConfigSubmitted, TwilioCallSubmitted,
};
