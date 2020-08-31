function InvalidConfigType() {
  this.message = 'The config type is invalid. It must either be \'channel\','
    + ' \'chain\', \'ui\' or \'other\'';
  this.code = 430;
}

function InvalidChainType() {
  this.message = 'The chain type is invalid. It must either be \'cosmos\' or '
    + '\'substrate\'';
  this.code = 431;
}

function MissingArgument(arg) {
  this.message = `Missing argument '${arg}'`;
  this.code = 432;
}

module.exports = { InvalidConfigType, InvalidChainType, MissingArgument };
