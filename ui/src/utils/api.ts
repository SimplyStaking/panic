import {API_URL, BASE_CHAINS} from "./constants"
import {raiseToast} from "./helpers";

/**
 * Fetches a list of base chains from the API.
 */
export function fetchBaseChains(): Promise<any> {
    // dummy implementation (we update this once new API is released)
    return new Promise((resolve) => {
        resolve(BASE_CHAINS);
    });
}

/**
 * This function will perform a call to an API V1 endpoint using the fetch API
 * and will display a success feedback if the call is successful, and an error
 * feedback otherwise.
 * @param toastSuccessMsg The message to be displayed if the request is
 * successful
 * @param toastErrorMsg The message to be displayed if the request errors
 * @param endpoint The name of the API v1 endpoint to be requested
 * @param requestProperties An object containing a list of properties to be
 * supplied to the fetch API
 */
export async function callApiV1EndpointWithFeedback(
    toastSuccessMsg: string, toastErrorMsg: string, endpoint: string,
    requestProperties?: RequestInit): Promise<[Response | undefined, boolean]> {

    let fullEndpoint: string = `${API_URL}/${endpoint}`;
    let response;
    let callFailed;
    try {
        response = await fetch(fullEndpoint, requestProperties);

        callFailed = !response.ok;

        callFailed ?
            raiseToast(toastErrorMsg, 2000, "danger")
            : raiseToast(toastSuccessMsg);
    } catch (e) {
        // If call raised an exception
        callFailed = true;
        raiseToast(toastErrorMsg, 2000, "danger");
    }

    return [response, callFailed];
}