import {API_URL} from "./constants";
import {PingPropertiesType, PingPropertiesTypeMultipleSources, PingResult} from "./types";

export const PingsAPI = {
    pingEndpoint: pingEndpoint,
    pingEndpointsConcurrently: pingEndpointsConcurrently
}

/**
 * Sends a post request to the given API endpoint with the given content as the body.
 * This function is generalised to cater for a number of pinging endpoints.
 * @param endpointUrl API endpoint to be called
 * @param content the content to be sent to the endpoint
 * @returns data object obtained from request sent, as a promise
 */
async function pingEndpoint(endpointUrl: string, content: PingPropertiesType): Promise<PingResult> {
    try {
        const pingReceived: Response = await fetch(
            `${API_URL}server/${endpointUrl}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(content)
            });
        return await pingReceived.json();
    } catch (error: any) {
        console.error(`Error getting ping from ${API_URL}${endpointUrl}`, error);
        return { error: '' }
    }
}

/**
 * Sends multiple post requests concurrently to the given API endpoint with the given content the body.
 * This function is generalised to cater for a number of pinging endpoints.
 * @param endpointUrl API endpoint to be called
 * @param contents an array of content objects to be sent with each request
 * @returns an array of data objects obtained from requests sent, as a promise
 */
async function pingEndpointsConcurrently(endpointUrl: string, contents: PingPropertiesTypeMultipleSources[]): Promise<PingResult[]> {
    const pings: Promise<PingResult>[] = contents.map((content) => pingEndpoint(endpointUrl, content));
    return await Promise.all(pings);
}
