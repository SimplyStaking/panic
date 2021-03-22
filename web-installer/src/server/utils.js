module.exports = {
  // These functions wrap a result on an error as an object
  resultJson: (result) => ({ result }),
  errorJson: (error) => ({ error }),

  SUCCESS_STATUS: 200,
  ERR_STATUS: 400,

  // Transforms a string representing a boolean as a boolean
  toBool: (boolStr) => ['true', 'yes', 'y'].some((element) => boolStr.toLowerCase()
    .includes(element)),

  // Checks which keys have values which are missing (null, undefined, '') in a
  // given object and returns an array of keys having missing values.
  missingValues: (values) => {
    const missingValuesList = [];
    Object.keys(values).forEach((param) => {
      if (!values[param]) {
        missingValuesList.push(param);
      }
    });
    return missingValuesList;
  },
};
