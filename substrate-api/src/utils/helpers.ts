import express from "express";
import {WsInterfacesManager} from "./api_interface";
import {errorJson, resultJson} from "./response";
import {BAD_REQ_STATUS, SERVER_ERR_STATUS, SUCCESS_STATUS} from "./constants";
import {
    CouldNotInitialiseConnection,
    LostConnectionWithNode,
    MissingKeysInQuery
} from "../errors/server";

export const apiCallExecutor = async (
    res: express.Response, wsInterfaces: WsInterfacesManager, websocket: any,
    apiCall: Function, params: any[], missingKeysList: string[]
) => {
    /**
     * This function is used as a helper to remove code duplication when
     * executing API calls. Note that params should not include the ApiPromise
     * instance as this is going to be obtained automatically from wsInterfaces
     */

    // Check that all required parameters have been sent
    if (missingKeysList.length !== 0) {
        const err = new MissingKeysInQuery(...missingKeysList);
        console.log(err.message);
        return res.status(BAD_REQ_STATUS).send(errorJson(
            {
                'message': err.message,
                'code': err.code
            }
        ));
    }

    // Initialise a connection, if there are errors when initialising, inform
    // the user accordingly. Note that here we are avoiding memory leaks by
    // relying on the fact that the manager does not overwrite connections for
    // the same websocket.
    if (!(await wsInterfaces.createInterface(websocket))) {
        let {api, provider} = wsInterfaces.wsInterfaces[websocket];
        try {
            let apiRet = resultJson(await apiCall.apply(
                this, [api, ...params]
            ));
            return res.status(SUCCESS_STATUS).send(apiRet);
        } catch (err: any) {
            // If an error was raised and the connection with the node is still
            // alive, inform the user with the error raised by the API. If not
            // inform the user that the node is down.
            if (provider.isConnected) {
                console.log(err.toString());
                return res.status(SERVER_ERR_STATUS).send(errorJson(
                    {
                        'message': err.message,
                        'code': null
                    }
                ))
            } else {
                const err = new LostConnectionWithNode(websocket);
                console.log(err.message);
                return res.status(SERVER_ERR_STATUS).send(errorJson(
                    {
                        'message': err.message,
                        'code': err.code
                    }
                ));
            }
        }
    } else {
        // If an error occurred while initialising a connection with the node
        // inform the user about this scenario
        const err = new CouldNotInitialiseConnection(websocket);
        console.log(err.message);
        return res.status(SERVER_ERR_STATUS).send(errorJson(
            {
                'message': err.message,
                'code': err.code
            }
        ));
    }
};

export const parseReqAndExecuteAPICall = async (
    req: express.Request, res: express.Response,
    wsInterfaces: WsInterfacesManager, apiCall: Function, params: string[]
) => {
    /**
     * This function is used as a helper to remove code duplication when
     * executing API calls. params should be a list of key names that are
     * expected to be passed as parameters in the query (excluding websocket).
     */

    console.log('Received request for %s', req.url);
    try {
        // extract the required parameters passed in the query
        let expectedParamsObject: { [index: string]: any } = {
            'websocket': req.query['websocket']
        };
        let expectedParamsList: any[] = [];
        params.forEach((param: string) => {
            expectedParamsObject[param] = req.query[param];
            expectedParamsList.push(req.query[param])
        });

        const missingKeysList: string[] = missingValues(expectedParamsObject);
        return await apiCallExecutor(
            res, wsInterfaces, expectedParamsObject['websocket'], apiCall,
            expectedParamsList, missingKeysList
        )
    } catch (err: any) {
        console.log(err);
        return res.status(SERVER_ERR_STATUS).send(errorJson(
            {
                'message': err.message,
                'code': null
            }
        ))
    }
};

// Checks which keys have values which are missing (null, undefined) in
// a given object and returns an array of keys having missing values.
export const missingValues = (object: { [id: string]: any }): string[] => {
    let missingValuesList: string[] = [];
    Object.keys(object).forEach((key) => {
        if (object[key] == null || object[key] == undefined) {
            missingValuesList.push(key);
        }
    });
    return missingValuesList;
};
