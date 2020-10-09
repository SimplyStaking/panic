const fs = require('fs');
const errors = require('./errors');

module.exports = {
  readFile: (filePath) => {
    let file;
    try {
      file = fs.readFileSync(filePath);
    } catch (err) {
      if (err.code === 'ENOENT') {
        throw new errors.MissingFile(filePath);
      } else {
        throw err;
      }
    }
    return file;
  },
};
