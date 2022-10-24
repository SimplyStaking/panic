import {WEIWATCHERS_MAPPING_URL} from "./constants";
import {SelectOptionType} from "@simply-vc/uikit/dist/types/types/select";

export const WeiWatchersAPI = {
    // panic-installer-sources
    weiWatchersMappingToSelectOptionType: weiWatchersMappingToSelectOptionType
}

/**
 * Sort the WeiWatchers based on the network name.
 * @param weiWatcherUrlMapping an Array of objects each containing
 * the network name and the url
 * @returns sorted Array of objects based on the network name.
 */
function sortWeiWatcherUrls(weiWatcherUrlMapping: Array<object>): Array<object> {
    const sortedWeiWatcherUrlMapping = [...weiWatcherUrlMapping]
    return sortedWeiWatcherUrlMapping.sort((url1, url2) => {
        return (url1['network'] > url2['network']) ? 1 : -1
    })
}

/**
 * Formats the Network/URL weiwatchers mappings to {@link SelectOptionType}.
 * The network is set as the label while the URL is set as the value.
 * @returns formatted weiwatchers mappings.
 */
async function weiWatchersMappingToSelectOptionType(): Promise<SelectOptionType> {
    const weiWatchersMapping = await getWeiWatchersMapping();
    const weiWatchersUrls = sortWeiWatcherUrls(weiWatchersMapping['urls']);
    return weiWatchersUrls.map((mapping) => {
        return {label: mapping['network'], value: mapping['url']}
    });
}

/**
 * Gets the wei watchers Network/URL mappings from the URL provided.
 * @returns the result from the mappings endpoints as a JSON object.
 */
async function getWeiWatchersMapping(): Promise<any> {
    try {
        const weiWatchersMapping: Response = await fetch(WEIWATCHERS_MAPPING_URL);
        const list = await weiWatchersMapping.json();
        return list;
    } catch (error: any) {
        console.log('Error getting weiwatchers mapping -', error);
        return {urls: []}
    }
}
