const axios = require('axios');

function fetchData(url, params) {
  return axios.get(url, { params });
}

export { fetchData };
