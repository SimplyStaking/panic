import {ApiPromise} from "@polkadot/api";
import {getSystemEvents} from "./query";
import express, {Express} from "express";
import {parseReqAndExecuteAPICall} from "../utils/helpers";
import {WsInterfacesManager} from "../utils/api_interface";

export const getSlashGetSlashedAmount = async (
    api: ApiPromise, blockHash: string, accountId: string
): Promise<number> => {
    let slashedAmount = 0;
    let events = await getSystemEvents(api, blockHash);
    // Check if there are any slashing events corresponding to the given account
    // address. If yes, add the amount and return it.
    for (const record of events) {
        const event = record.event;
        if (event.section.toLowerCase() === 'staking'
            && event.method.toLowerCase() == 'slashed') {
            const eventData = JSON.parse(JSON.stringify(event.data));
            if (eventData[0] === accountId) {
                // If the value is string, then it is a hex number, thus convert
                // to decimal. Otherwise, no conversion is needed.
                if (typeof eventData[1] === 'string') {
                    slashedAmount += parseInt(eventData[1], 16);
                } else {
                    slashedAmount += eventData[1];
                }
            }
        }
    }
    return slashedAmount;
};

export const getOfflineIsOffline = async (
    api: ApiPromise, blockHash: string, accountId: string
): Promise<boolean> => {
    let events = await getSystemEvents(api, blockHash);
    // Check if the accountId is listed in any SomeOffline event. If yes return
    // true, otherwise return false.
    for (const record of events) {
        const event = record.event;
        if (event.section.toLowerCase() === 'imonline'
            && event.method.toLowerCase() == 'someoffline') {
            const eventData = JSON.parse(JSON.stringify(event.data));
            for (const validatorData of eventData[0]) {
                if (validatorData[0] === accountId) {
                    return true
                }
            }
        }
    }
    return false;
};

export const customInterface = (
    app: Express, wsInterfaces: WsInterfacesManager
) => {

    // This endpoint requires the websocket url of the node to connect with, the
    // hash of the block to query, and the account Id (stash) to look out for.
    app.get('/api/custom/slash/getSlashedAmount', async (
        req: express.Request, res: express.Response
    ) => {
        return await parseReqAndExecuteAPICall(req, res, wsInterfaces,
            getSlashGetSlashedAmount, ['blockHash', 'accountId'])
    });

    // This endpoint requires the websocket url of the node to connect with, the
    // hash of the block to query, and the account Id (stash) to look out for.
    app.get('/api/custom/offline/isOffline', async (
        req: express.Request, res: express.Response
    ) => {
        return await parseReqAndExecuteAPICall(req, res, wsInterfaces,
            getOfflineIsOffline, ['blockHash', 'accountId'])
    });
};
