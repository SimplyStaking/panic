import express from "express";
import {BaseChain} from "../../../../../entities/ts/BaseChain";
import {CouldNotRetrieveDataFromDB, NotFoundWarning} from "../../../constant/server.feedback";
import {ResponseError, ResponseSuccess} from "../../entity/io/ResponseData";
import {BaseChainRepository} from "../../entity/repository/BaseChainRepository";

/**
 * Resource Controller for Panic Base Chains
 */
export class BaseChainResource {

    private repo: BaseChainRepository = null;

    constructor() {
        this.repo = new BaseChainRepository();
    }

    /**
     * Get a list of base chains from Database in base chain collection
     *
     * @param req Request from Express
     * @param res Response from Express
     */
    public async getAll(req: express.Request,
                        res: express.Response): Promise<void> {
        try {
            const baseChains = await this.repo.findAllAndDeepPopulate([
                'sources', 'severity_alerts', 'threshold_alerts', 'time_window_alerts'
            ], {path: 'severity_alerts', populate: {path: 'type'}});

            const response = new ResponseSuccess<BaseChain[]>(res);
            response.send(baseChains);
        } catch (err: any) {
            console.error(err);
            const error = new CouldNotRetrieveDataFromDB();
            const response = new ResponseError(res, error);
            response.send();
        }
    }

    /**
     * Get base chain by id from Database in base chain collection
     *
     * @param req Request from Express
     * @param res Response from Express
     */
    public async getItem(req: express.Request,
                         res: express.Response): Promise<void> {
        try {
            const baseChain = await this.getBaseChainById(res, req.params.id);
            if (baseChain instanceof ResponseError) {
                baseChain.send();
                return;
            }

            const response = new ResponseSuccess<BaseChain>(res);
            response.send(baseChain);
        } catch (err: any) {
            console.error(err);
            const error = new CouldNotRetrieveDataFromDB();
            const response = new ResponseError(res, error);
            response.send();
        }
    }

    /**
     * Get base chain by ID, if not found send a `NotFoundWarning` over Response Error instance.
     *
     * @param res Response from Express
     * @param id base chain id
     */
    private async getBaseChainById(res: express.Response, id: string): Promise<BaseChain | ResponseError> {
        const baseChain = await this.repo.findOneByIdAndDeepPopulate(id, [
            'sources', 'severity_alerts', 'threshold_alerts', 'time_window_alerts'
        ], {path: 'severity_alerts', populate: {path: 'type'}});
        if (!baseChain) {
            return new ResponseError(res, new NotFoundWarning());
        }

        return baseChain;
    }
}
