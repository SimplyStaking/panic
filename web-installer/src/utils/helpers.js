/**
 * Helper function to reduce code duplication when removing a chain
 * and all it's data.
 * @param currentConfig is the current configuration of the chain
 * @param stateData is the data of the Channel which is in redux state
 * @param chainID is the identifier of the current chain which is being deleted
 * @param removeDetails is the function which is used to remove the channel data from the chain
 */
export function clearChannelData(currentConfig, stateData, chainID, removeDetails) {
  let payload = {};
  let index = 0;
  for (let i = 0; i < stateData.allIds.length; i += 1) {
    payload = JSON.parse(JSON.stringify(stateData.byId[stateData.allIds[i]]));
    if (payload.parent_ids.includes(chainID)) {
      index = payload.parent_ids.indexOf(chainID);
      if (index > -1) {
        payload.parent_ids.splice(index, 1);
      }
      index = payload.parent_names.indexOf(currentConfig.chain_name);
      if (index > -1) {
        payload.parent_names.splice(index, 1);
      }
      removeDetails(payload);
    }
  }
}

/**
 * Helper function to reduce code duplication when removing a chain
 * and all it's data.
 * @param currentConfig is the current configuration of the chain
 * @param type this is the type of data we are going to be removing
 * @param removeDetails is the function which is used to remove the data source from the chain
 */
export function clearDataSources(currentConfig, type, removeDataSourceDetails, payload) {
  for (let i = 0; i < currentConfig[type].length; i += 1) {
    // eslint-disable-next-line no-param-reassign
    payload.id = currentConfig[type][i];
    removeDataSourceDetails(payload);
  }
}
