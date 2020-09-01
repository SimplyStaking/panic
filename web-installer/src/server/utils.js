module.exports = {
  resultJson: result => ({ result }),
  errorJson: error => ({ error }),

  SUCCESS_STATUS: 200,
  ERR_STATUS: 400,

  toBool: boolStr => ['true', 'yes', 'y'].some(element => boolStr.toLowerCase()
    .includes(element)),
};
