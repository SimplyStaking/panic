import express, {Express} from "express";
import {WsInterfacesManager} from "../utils/api_interface";
import {TIMEOUT_TIME_MS} from "../utils/constants";
import {ApiPromise} from "@polkadot/api";
import {callFnWithTimeoutSafely} from "../utils/timeout";
import {apiCallTimeoutFail} from "../utils/msgs";
import {parseReqAndExecuteAPICall} from "../utils/helpers";

export const getSystemHealth = async (api: ApiPromise): Promise<any> => {
    return await callFnWithTimeoutSafely(
        api.rpc.system.health, [], TIMEOUT_TIME_MS,
        apiCallTimeoutFail('system/health')
    );
};

export const getSystemProperties = async (api: ApiPromise): Promise<any> => {
    return await callFnWithTimeoutSafely(
        api.rpc.system.properties, [], TIMEOUT_TIME_MS,
        apiCallTimeoutFail('system/properties')
    );
};

export const getSystemSyncState = async (api: ApiPromise): Promise<any> => {
    return await callFnWithTimeoutSafely(
        api.rpc.system.syncState, [], TIMEOUT_TIME_MS,
        apiCallTimeoutFail('system/syncState')
    );
};

export const getChainFinalizedHead = async (api: ApiPromise): Promise<any> => {
    return await callFnWithTimeoutSafely(
        api.rpc.chain.getFinalizedHead, [], TIMEOUT_TIME_MS,
        apiCallTimeoutFail('chain/getFinalizedHead')
    );
};

export const getChainGetHeader = async (
    api: ApiPromise, blockHash: string
): Promise<any> => {
    return await callFnWithTimeoutSafely(
        api.rpc.chain.getHeader, [blockHash], TIMEOUT_TIME_MS,
        apiCallTimeoutFail('chain/getHeader')
    );
};

export const getChainGetBlockHash = async (
    api: ApiPromise, blockNumber: number
): Promise<any> => {
    return await callFnWithTimeoutSafely(
        api.rpc.chain.getBlockHash, [blockNumber], TIMEOUT_TIME_MS,
        apiCallTimeoutFail('chain/getBlockHash')
    );
};

export const rpcInterface = (
    app: Express, wsInterfaces: WsInterfacesManager
) => {

    // This endpoint only requires the websocket url of the node to connect with
    app.get('/api/rpc/system/health', async (
        req: express.Request, res: express.Response
    ) => {
        return await parseReqAndExecuteAPICall(req, res, wsInterfaces,
            getSystemHealth, [])
    });

    // This endpoint only requires the websocket url of the node to connect with
    app.get('/api/rpc/system/properties', async (
        req: express.Request, res: express.Response
    ) => {
        return await parseReqAndExecuteAPICall(req, res, wsInterfaces,
            getSystemProperties, [])
    });

    // This endpoint only requires the websocket url of the node to connect with
    app.get('/api/rpc/system/syncState', async (
        req: express.Request, res: express.Response
    ) => {
        return await parseReqAndExecuteAPICall(req, res, wsInterfaces,
            getSystemSyncState, [])
    });

    // This endpoint only requires the websocket url of the node to connect with
    app.get('/api/rpc/chain/getFinalizedHead', async (
        req: express.Request, res: express.Response
    ) => {
        return await parseReqAndExecuteAPICall(req, res, wsInterfaces,
            getChainFinalizedHead, [])
    });

    // This endpoint requires the websocket url of the node to connect with and
    // the hash of the block whose header is to be obtained
    app.get('/api/rpc/chain/getHeader', async (
        req: express.Request, res: express.Response
    ) => {
        return await parseReqAndExecuteAPICall(req, res, wsInterfaces,
            getChainGetHeader, ['blockHash'])
    });

    // This endpoint requires the websocket url of the node to connect with and
    // the height of the block whose hash is to be obtained
    app.get('/api/rpc/chain/getBlockHash', async (
        req: express.Request, res: express.Response
    ) => {
        return await parseReqAndExecuteAPICall(req, res, wsInterfaces,
            getChainGetBlockHash, ['blockNumber'])
    });
};
