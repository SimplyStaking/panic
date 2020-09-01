function ConfigSubmitted(config, path) {
  this.message = `${config} submitted in ${path}.`;
}

module.exports = {
  ConfigSubmitted,
};
