import {ApiPromise} from "@polkadot/api";
import {callFnWithTimeoutSafely} from "../utils/timeout";
import {HEAVY_TIMEOUT_TIME_MS, TIMEOUT_TIME_MS} from "../utils/constants";
import {apiCallTimeoutFail} from "../utils/msgs";
import express, {Express} from "express";
import {WsInterfacesManager} from "../utils/api_interface";
import {parseReqAndExecuteAPICall} from "../utils/helpers";

export const getDemocracyReferendums = async (api: ApiPromise):
    Promise<any> => {
    return await callFnWithTimeoutSafely(
        api.derive.democracy.referendums, [], HEAVY_TIMEOUT_TIME_MS,
        apiCallTimeoutFail('democracy/referendums')
    );
};

export const getDemocracyProposals = async (api: ApiPromise): Promise<any> => {
    return await callFnWithTimeoutSafely(
        api.derive.democracy.proposals, [], HEAVY_TIMEOUT_TIME_MS,
        apiCallTimeoutFail('democracy/proposals')
    );
};

export const getStakingValidators = async (api: ApiPromise): Promise<any> => {
    return await callFnWithTimeoutSafely(
        api.derive.staking.validators, [], TIMEOUT_TIME_MS,
        apiCallTimeoutFail('staking/validators')
    );
};

export const deriveInterface = (
    app: Express, wsInterfaces: WsInterfacesManager
) => {

    // This endpoint only requires the websocket url of the node to connect with
    app.get('/api/derive/democracy/proposals', async (
        req: express.Request, res: express.Response
    ) => {
        return await parseReqAndExecuteAPICall(req, res, wsInterfaces,
            getDemocracyProposals, [])
    });

    // This endpoint only requires the websocket url of the node to connect with
    app.get('/api/derive/democracy/referendums', async (
        req: express.Request, res: express.Response
    ) => {
        return await parseReqAndExecuteAPICall(req, res, wsInterfaces,
            getDemocracyReferendums, [])
    });

    // This endpoint only requires the websocket url of the node to connect with
    app.get('/api/derive/staking/validators', async (
        req: express.Request, res: express.Response
    ) => {
        return await parseReqAndExecuteAPICall(req, res, wsInterfaces,
            getStakingValidators, [])
    });
};
