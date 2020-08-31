module.exports = {
  toBool: boolStr => ['true', 'yes', 'y'].some(element => boolStr.toLowerCase()
    .includes(element)),
};
