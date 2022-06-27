import {ApiPromise, WsProvider} from "@polkadot/api";

export interface WsInterface {
    api: ApiPromise,
    provider: WsProvider
}

export interface WsInterfaces {
    [key: string]: WsInterface
}
