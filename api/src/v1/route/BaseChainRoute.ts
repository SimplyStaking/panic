import * as core from 'express-serve-static-core';
import {BaseChainResource} from "../rest/basechain/BaseChainResource";

/**
 * Base Chain routes
 */
export class BaseChainRoute {

    public constructor(app: core.Express) {
        const baseChain = new BaseChainResource();

        app.get('/v1/basechains', baseChain.getAll.bind(baseChain));
        app.get('/v1/basechains/:id', baseChain.getItem.bind(baseChain));
    }
}
