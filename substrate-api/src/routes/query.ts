import express, {Express} from "express";
import {WsInterfacesManager} from "../utils/api_interface";
import {TIMEOUT_TIME_MS} from "../utils/constants";
import {ApiPromise} from "@polkadot/api";
import {callFnWithTimeoutSafely} from "../utils/timeout";
import {apiCallTimeoutFail} from "../utils/msgs";
import {parseReqAndExecuteAPICall} from "../utils/helpers";

export const getDemocracyReferendumInfoOf = async (
    api: ApiPromise, referendumIndex: number
): Promise<any> => {
    return await callFnWithTimeoutSafely(
        api.query.democracy.referendumInfoOf, [referendumIndex],
        TIMEOUT_TIME_MS, apiCallTimeoutFail('democracy/referendumInfoOf')
    );
};

export const getDemocracyReferendumCount = async (api: ApiPromise):
    Promise<any> => {
    return await callFnWithTimeoutSafely(
        api.query.democracy.referendumCount, [], TIMEOUT_TIME_MS,
        apiCallTimeoutFail('democracy/referendumCount')
    );
};

export const getDemocracyPublicProps = async (api: ApiPromise):
    Promise<any> => {
    return await callFnWithTimeoutSafely(
        api.query.democracy.publicProps, [], TIMEOUT_TIME_MS,
        apiCallTimeoutFail('democracy/publicProps')
    );
};

export const getDemocracyPublicPropCount = async (api: ApiPromise):
    Promise<any> => {
    return await callFnWithTimeoutSafely(
        api.query.democracy.publicPropCount, [], TIMEOUT_TIME_MS,
        apiCallTimeoutFail('democracy/publicPropCount')
    );
};

export const getDemocracyDepositOf = async (api: ApiPromise, propIndex: number):
    Promise<any> => {
    return await callFnWithTimeoutSafely(
        api.query.democracy.depositOf, [propIndex], TIMEOUT_TIME_MS,
        apiCallTimeoutFail('democracy/depositOf')
    );
};

export const getGrandpaStalled = async (api: ApiPromise): Promise<any> => {
    return await callFnWithTimeoutSafely(
        api.query.grandpa.stalled, [], TIMEOUT_TIME_MS,
        apiCallTimeoutFail('grandpa/stalled')
    );
};

export const getSessionCurrentIndex = async (api: ApiPromise): Promise<any> => {
    return await callFnWithTimeoutSafely(
        api.query.session.currentIndex, [], TIMEOUT_TIME_MS,
        apiCallTimeoutFail('session/currentIndex')
    );
};

export const getSessionValidators = async (api: ApiPromise): Promise<any> => {
    return await callFnWithTimeoutSafely(
        api.query.session.validators, [], TIMEOUT_TIME_MS,
        apiCallTimeoutFail('session/validators')
    );
};

export const getSessionDisabledValidators = async (
    api: ApiPromise
): Promise<any> => {
    return await callFnWithTimeoutSafely(
        api.query.session.disabledValidators, [], TIMEOUT_TIME_MS,
        apiCallTimeoutFail('session/disabledValidators')
    );
};

export const getImOnlineAuthoredBlocks = async (
    api: ApiPromise, sessionIndex: number, accountId: string
): Promise<any> => {
    return await callFnWithTimeoutSafely(
        api.query.imOnline.authoredBlocks, [sessionIndex, accountId],
        TIMEOUT_TIME_MS, apiCallTimeoutFail('imOnline/authoredBlocks')
    );
};

export const getImOnlineReceivedHeartbeats = async (
    api: ApiPromise, sessionIndex: number, authIndex: number
): Promise<any> => {
    return await callFnWithTimeoutSafely(
        api.query.imOnline.receivedHeartbeats, [sessionIndex, authIndex],
        TIMEOUT_TIME_MS, apiCallTimeoutFail('imOnline/receivedHeartbeats')
    );
};

export const getStakingActiveEra = async (api: ApiPromise): Promise<any> => {
    return await callFnWithTimeoutSafely(
        api.query.staking.activeEra, [], TIMEOUT_TIME_MS,
        apiCallTimeoutFail('staking/activeEra')
    );
};

export const getStakingErasStakers = async (
    api: ApiPromise, eraIndex: number, accountId: string
): Promise<any> => {
    return await callFnWithTimeoutSafely(
        api.query.staking.erasStakers, [eraIndex, accountId], TIMEOUT_TIME_MS,
        apiCallTimeoutFail('staking/erasStakers')
    );
};

export const getStakingErasRewardPoints = async (
    api: ApiPromise, eraIndex: number
): Promise<any> => {
    return await callFnWithTimeoutSafely(
        api.query.staking.erasRewardPoints, [eraIndex], TIMEOUT_TIME_MS,
        apiCallTimeoutFail('staking/erasRewardPoints')
    );
};

export const getStakingLedger = async (
    api: ApiPromise, accountId: string
): Promise<any> => {
    return await callFnWithTimeoutSafely(
        api.query.staking.ledger, [accountId], TIMEOUT_TIME_MS,
        apiCallTimeoutFail('staking/ledger')
    );
};

export const getStakingHistoryDepth = async (api: ApiPromise): Promise<any> => {
    return await callFnWithTimeoutSafely(
        api.query.staking.historyDepth, [], TIMEOUT_TIME_MS,
        apiCallTimeoutFail('staking/historyDepth')
    );
};

export const getStakingBonded = async (
    api: ApiPromise, accountId: string
): Promise<any> => {
    return await callFnWithTimeoutSafely(
        api.query.staking.bonded, [accountId], TIMEOUT_TIME_MS,
        apiCallTimeoutFail('staking/bonded')
    );
};

export const getSystemEvents = async (
    api: ApiPromise, blockHash: string
): Promise<any> => {
    return await callFnWithTimeoutSafely(
        api.query.system.events.at, [blockHash], TIMEOUT_TIME_MS,
        apiCallTimeoutFail('system/events')
    );
};

export const queryInterface = (
    app: Express, wsInterfaces: WsInterfacesManager
) => {

    // This endpoint only requires the websocket url of the node to connect with
    app.get('/api/query/grandpa/stalled', async (
        req: express.Request, res: express.Response
    ) => {
        return await parseReqAndExecuteAPICall(req, res, wsInterfaces,
            getGrandpaStalled, [])
    });

    // This endpoint requires the websocket url of the node to connect with and
    // the proposal index
    app.get('/api/query/democracy/depositOf', async (
        req: express.Request, res: express.Response
    ) => {
        return await parseReqAndExecuteAPICall(req, res, wsInterfaces,
            getDemocracyDepositOf, ['propIndex'])
    });

    // This endpoint only requires the websocket url of the node to connect with
    app.get('/api/query/democracy/publicPropCount', async (
        req: express.Request, res: express.Response
    ) => {
        return await parseReqAndExecuteAPICall(req, res, wsInterfaces,
            getDemocracyPublicPropCount, [])
    });

    // This endpoint only requires the websocket url of the node to connect with
    app.get('/api/query/democracy/publicProps', async (
        req: express.Request, res: express.Response
    ) => {
        return await parseReqAndExecuteAPICall(req, res, wsInterfaces,
            getDemocracyPublicProps, [])
    });

    // This endpoint only requires the websocket url of the node to connect with
    app.get('/api/query/democracy/referendumCount', async (
        req: express.Request, res: express.Response
    ) => {
        return await parseReqAndExecuteAPICall(req, res, wsInterfaces,
            getDemocracyReferendumCount, [])
    });

    // This endpoint requires the websocket url of the node to connect with and
    // the referendum index
    app.get('/api/query/democracy/referendumInfoOf', async (
        req: express.Request, res: express.Response
    ) => {
        return await parseReqAndExecuteAPICall(req, res, wsInterfaces,
            getDemocracyReferendumInfoOf, ['referendumIndex'])
    });

    // This endpoint only requires the websocket url of the node to connect with
    app.get('/api/query/session/currentIndex', async (
        req: express.Request, res: express.Response
    ) => {
        return await parseReqAndExecuteAPICall(req, res, wsInterfaces,
            getSessionCurrentIndex, [])
    });

    // This endpoint only requires the websocket url of the node to connect with
    app.get('/api/query/session/validators', async (
        req: express.Request, res: express.Response
    ) => {
        return await parseReqAndExecuteAPICall(req, res, wsInterfaces,
            getSessionValidators, [])
    });

    // This endpoint only requires the websocket url of the node to connect with
    app.get('/api/query/session/disabledValidators', async (
        req: express.Request, res: express.Response
    ) => {
        return await parseReqAndExecuteAPICall(req, res, wsInterfaces,
            getSessionDisabledValidators, [])
    });

    // This endpoint requires the websocket url of the node to connect with, the
    // index of the session to be queried, and the accountId of the authority
    // (stash).
    app.get('/api/query/imOnline/authoredBlocks', async (
        req: express.Request, res: express.Response
    ) => {
        return await parseReqAndExecuteAPICall(req, res, wsInterfaces,
            getImOnlineAuthoredBlocks, ['sessionIndex', 'accountId'])
    });

    // This endpoint requires the websocket url of the node to connect with, the
    // index of the session to be queried, and the index of the authority in the
    // active set.
    app.get('/api/query/imOnline/receivedHeartbeats', async (
        req: express.Request, res: express.Response
    ) => {
        return await parseReqAndExecuteAPICall(req, res, wsInterfaces,
            getImOnlineReceivedHeartbeats, ['sessionIndex', 'authIndex'])
    });

    // This endpoint only requires the websocket url of the node to connect with
    app.get('/api/query/staking/activeEra', async (
        req: express.Request, res: express.Response
    ) => {
        return await parseReqAndExecuteAPICall(req, res, wsInterfaces,
            getStakingActiveEra, [])
    });

    // This endpoint requires the websocket url of the node to connect with,
    // the era index and the accountId (stash) of the authority.
    app.get('/api/query/staking/erasStakers', async (
        req: express.Request, res: express.Response
    ) => {
        return await parseReqAndExecuteAPICall(req, res, wsInterfaces,
            getStakingErasStakers, ['eraIndex', 'accountId'])
    });

    // This endpoint requires the websocket url of the node to connect with and
    // the era index.
    app.get('/api/query/staking/erasRewardPoints', async (
        req: express.Request, res: express.Response
    ) => {
        return await parseReqAndExecuteAPICall(req, res, wsInterfaces,
            getStakingErasRewardPoints, ['eraIndex'])
    });

    // This endpoint requires the websocket url of the node to connect with and
    // the accountId (stash) of the authority.
    app.get('/api/query/staking/ledger', async (
        req: express.Request, res: express.Response
    ) => {
        return await parseReqAndExecuteAPICall(req, res, wsInterfaces,
            getStakingLedger, ['accountId'])
    });

    // This endpoint only requires the websocket url of the node to connect with
    app.get('/api/query/staking/historyDepth', async (
        req: express.Request, res: express.Response
    ) => {
        return await parseReqAndExecuteAPICall(req, res, wsInterfaces,
            getStakingHistoryDepth, [])
    });

    // This endpoint requires the websocket url of the node to connect with and
    // the accountId (stash) of the authority.
    app.get('/api/query/staking/bonded', async (
        req: express.Request, res: express.Response
    ) => {
        return await parseReqAndExecuteAPICall(req, res, wsInterfaces,
            getStakingBonded, ['accountId'])
    });

    // This endpoint requires the websocket url of the node to connect with and
    // the hash of the block whose events are to be queried.
    app.get('/api/query/system/events', async (
        req: express.Request, res: express.Response
    ) => {
        return await parseReqAndExecuteAPICall(req, res, wsInterfaces,
            getSystemEvents, ['blockHash'])
    });
};
