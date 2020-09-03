function ConfigSubmitted(config, path) {
  this.message = `${config} submitted in ${path}.`;
}

function TwilioCallSubmitted(phoneNumber) {
  this.message = `Twilio call to ${phoneNumber} submitted.`;
}

function EmailSubmitted(email) {
  this.message = `Email to ${email} submitted.`;
}

function TestEmail() {
  this.subject = 'Test Email from PANIC';
  this.text = 'Test Email from PANIC';
}

module.exports = {
  ConfigSubmitted, TwilioCallSubmitted, EmailSubmitted, TestEmail,
};
