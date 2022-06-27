import {ApiOptions} from "@polkadot/api/types";

export class TestWsProvider {
    // This class is used as a dummy to replace polkadot-js WsProviders when
    // mocking

    private readonly wsUrl;
    private _isConnected;

    constructor(wsUrl: string) {
        this.wsUrl = wsUrl;
        this._isConnected = true
    }

    get isConnected() {
        return this._isConnected;
    }

    disconnect() {
        this._isConnected = false
    }
}

export class TestApiPromise {
    // This class is used as a dummy to replace polkadot-js ApiPromises when
    // mocking

    private readonly wsUrl;

    constructor(wsUrl: string) {
        this.wsUrl = wsUrl
    }

    static create(options?: ApiOptions) {
    }
}
