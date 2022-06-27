import {ApiPromise, WsProvider} from '@polkadot/api';
import {callFnWithTimeoutSafely} from "./timeout";
import {TIMEOUT_TIME_MS} from "./constants";
import {WsInterface, WsInterfaces} from "../types/api_interface";

export const initialiseWsInterface = async (wsUrl: string):
    Promise<undefined | WsInterface> => {
    /**
     * This function will attempt to connect with the node having websocket
     * wsUrl and returns the provider and API instances if the connection is
     * successful. If the connection is not successful for TIMEOUT_TIME_MS, then
     * the connection attempt is dismissed and nothing is returned by the
     * function.
     */
    console.log(`Connecting to ${wsUrl}`);
    let provider;
    try {
        // connect to the WebSocket once and reuse that connection
        provider = new WsProvider(wsUrl);

        // open an API connection with the provider
        let api = await callFnWithTimeoutSafely(
            ApiPromise.create, [{provider}], TIMEOUT_TIME_MS,
            'Connection could not be established.'
        );
        console.log(`Connection with ${wsUrl} successful`);

        return {api: api, provider: provider};
    } catch (e: any) {
        console.log(`Could not connect with ${wsUrl}. ${e.toString()}`);

        // If the connection exists but the API could not be initialised
        // disconnect the connection to avoid having leaked promises.
        if (provider) {
            await provider.disconnect()
        }
    }
};

export class WsInterfacesManager {
    /**
     * This class manages the set of ws interfaces. The following JSON is
     * stored by the manager: {<wsUrl>: {api: <api>, provider: <provider>} }
     */
    private readonly _wsInterfaces: WsInterfaces;

    constructor() {
        this._wsInterfaces = {};
    }

    get wsInterfaces(): WsInterfaces {
        return this._wsInterfaces
    }

    async createInterface(wsUrl: string): Promise<boolean> {
        /**
         * This function attempts to create a new interface for the given wsUrl.
         * If there are errors while initialising, this function returns true.
         * NOTE: This function does not create a new instance if there is
         *     : already one declared
         */
        if (wsUrl in this._wsInterfaces && this._wsInterfaces[wsUrl]) {
            return false
        }

        try {
            let initReturn = await initialiseWsInterface(wsUrl);
            if (initReturn) {
                this._wsInterfaces[wsUrl] = initReturn;
                return false
            } else {
                console.log(
                    `Error while initialising a websocket interface for ${
                        wsUrl}`
                );
                return true
            }
        } catch (e: any) {
            console.log(`Error while initialising a websocket interface for ${
                wsUrl}. ${e.toString()}`);
            return true
        }
    }

    async removeInterface(wsUrl: string): Promise<boolean> {
        /**
         * This function attempts to disconnect the interface from the node and
         * removes the interface from the state. If there are errors during the
         * procedure, this function returns true.
         * NOTE: This is only done if a WsInterface exists for the wsUrl
         */
        if (!(wsUrl in this._wsInterfaces && this._wsInterfaces[wsUrl])) {
            return false
        }

        try {
            let {provider} = this._wsInterfaces[wsUrl];
            await provider.disconnect();
            delete this._wsInterfaces[wsUrl];
            return false
        } catch (e: any) {
            console.log(`Error while removing interface for ${
                wsUrl}. ${e.toString()}`);
            return true
        }
    }

}
