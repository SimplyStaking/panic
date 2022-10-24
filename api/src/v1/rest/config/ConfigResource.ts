import express from "express";
import {ObjectID} from "mongodb";
import mongoose, {Document} from "mongoose";
import {Config} from "../../../../../entities/ts/Config";
import {GenericDocument} from "../../../constant/mongoose";
import {
    CouldNotRemoveDataFromDB,
    CouldNotRetrieveDataFromDB,
    CouldNotSaveDataToDB,
    DuplicateWarning,
    InvalidIDError,
    MissingParameterWarning,
    NotFoundWarning,
    ValidationDataError
} from "../../../constant/server.feedback";
import {MongooseUtil} from "../../../util/MongooseUtil";
import {ResponseError, ResponseNoContent, ResponseSuccess}
    from "../../entity/io/ResponseData";
import {ConfigModel} from "../../entity/model/ConfigModel";
import {ConfigRepository} from "../../entity/repository/ConfigRepository";
import {BaseChainRepository}
    from "../../entity/repository/BaseChainRepository";
import {ObjectUtil} from "../../../util/ObjectUtil";
import {EmailRepository} from "../../entity/repository/ChannelRepository";
import {ConfigOldModel} from "../../entity/model/ConfigOldModel";

/**
 * Resource Controller for Panic Configuration
 */
export class ConfigResource {
    private configRepo: ConfigRepository = null;
    private baseChainRepo: BaseChainRepository = null;
    private channelRepo: EmailRepository = null;

    constructor() {
        this.configRepo = new ConfigRepository();
        this.baseChainRepo = new BaseChainRepository();
        this.channelRepo = new EmailRepository();
    }

    /**
     * Get a list of Configurations from Database in config collection
     *
     * @param req Request from Express
     * @param res Response from Express
     */
    public async getAll(req: express.Request,
                        res: express.Response): Promise<void> {
        try {
            const configs = await this.configRepo.findAll();

            const response = new ResponseSuccess<Config[]>(res);
            response.send(configs);
        } catch (err: any) {
            console.error(err);
            const error = new CouldNotRetrieveDataFromDB();
            const response = new ResponseError(res, error);
            response.send();
        }
    }

    /**
     * Get configuration by id from Database in config collection
     *
     * @param req Request from Express
     * @param res Response from Express
     */
    public async getItem(req: express.Request,
        res: express.Response): Promise<void> {
        try {
            const responseError = this.isMissingParam(req, res);
            if (responseError instanceof ResponseError) {
                responseError.send();
                return;
            }

            const config = await this.getConfigById(res, req.params.id);
            if (config instanceof ResponseError) {
                config.send();
                return;
            }

            const response = new ResponseSuccess<Config>(res);
            response.send(config);
        } catch (err: any) {
            console.error(err);
            const error = new CouldNotRetrieveDataFromDB();
            const response = new ResponseError(res, error);
            response.send();
        }
    }

    /**
     * Create a new Configuration on the Database in the config collection
     *
     * @param req Request from Express
     * @param res Response from Express
     */
    public async create(req: express.Request,
        res: express.Response): Promise<void> {
        try {
            const invalidFields = [
                'threshold_alerts', 'severity_alerts', 'time_window_alerts'
            ];
            
            let config: Config = MongooseUtil.merge(
                new Config(), req.body, invalidFields);

            // subChain name duplication validation
            let duplicate = await this.configRepo.isDuplicateSubChain(config);
            if (duplicate) {
                const response = new ResponseError(
                    res, new DuplicateWarning('subChain.name'));
                response.send();
                return;
            }

            let baseChain = await this.baseChainRepo.findOneByIdAndDeepPopulate(
                req.body.baseChain.id || req.body.baseChain,
                ['severity_alerts', 'threshold_alerts', 'time_window_alerts']);

            baseChain = ObjectUtil.snakeToCamel(baseChain.toJSON());

            // populate alerts with baseChains alerts
            config.thresholdAlerts = baseChain.thresholdAlerts;
            config.severityAlerts = baseChain.severityAlerts;
            config.timeWindowAlerts = baseChain.timeWindowAlerts;

            const model: Document<Config> = new ConfigModel(config.toJSON());
            await this.save(res, model);
        } catch (err: any) {
            console.error(err);
            const error = new CouldNotSaveDataToDB();
            const response = new ResponseError(res, error);
            response.send();
        }
    }

    /**
     * Updates an existing configuration on the Database in the config
     * collection
     *
     * @param req Request from Express
     * @param res Response from Express
     */
    public async update(req: express.Request,
                        res: express.Response): Promise<void> {
        try {
            const responseError = this.isMissingParam(req, res);
            if (responseError instanceof ResponseError) {
                responseError.send();
                return;
            }

            // to avoid updating baseChain on update
            delete req.body.baseChain;

            // subChain name duplication validation
            let duplicate = await this.configRepo.isDuplicateSubChain({
                ...req.body,
                id: req.params.id
            } as Config);

            if (duplicate) {
                const response = new ResponseError(res,
                    new DuplicateWarning('subChain.name'));
                response.send();
                return;
            }

            const config: Document<Config> = await this.getConfigById(res,
                req.params.id) as any;
            if (config instanceof ResponseError) {
                config.send();
                return;
            }

            await this.createBkp(config);

            const request = ObjectUtil.deepCamelToSnake(req.body);
            const model: Document = MongooseUtil.merge(config, request);

            await this.save(res, model);
        } catch (err: any) {
            console.error(err);
            const error = new CouldNotSaveDataToDB();
            const response = new ResponseError(res, error);
            response.send();
        }
    }

    /**
     * Removes configuration by id on Database in config collection
     *
     * @param req Request from Express
     * @param res Response from Express
     */
    public async remove(req: express.Request,
                        res: express.Response): Promise<void> {
        try {
            const responseError = this.isMissingParam(req, res);
            if (responseError instanceof ResponseError) {
                responseError.send();
                return;
            }

            const config = await this.configRepo.findOneById(req.params.id);
            await this.createBkp(config as any);

            const isDeleted = await this.configRepo
                                        .deleteOneById(req.params.id);
            console.log(isDeleted);                                        
            if (!isDeleted) {
                const response = new ResponseError(res, new NotFoundWarning());
                response.send();
                return;
            }            

            await this.channelRepo.unlinkConfigFromAllChannels(req.params.id);

            const response = new ResponseNoContent(res);
            response.send();
        } catch (err: any) {
            console.error(err);
            const error = new CouldNotRemoveDataFromDB();
            const response = new ResponseError(res, error);
            response.send();
        }
    }

    /**
     * Checks if there are missing params
     *
     * @param req Request from Express
     * @param res Response from Express
     */
    private isMissingParam(req: express.Request,
                           res: express.Response): ResponseError {
        if (!req.params.id) {
            const error = new MissingParameterWarning('id');

            return new ResponseError(res, error);
        }

        return null;
    }

    /**
     * Save document on config collection. If an error occurs, an error response
     * is sent via `res`.
     *
     * @param res Response from Express
     * @param model The config document object
     */
    private async save(res: express.Response, model: Document<Config>): 
        Promise<void> {

        model.set('config_type', new ObjectID(
            GenericDocument.CONFIG_TYPE_SUB_CHAIN)
        );

        const isValid = await MongooseUtil.isValid(model);
        if (!isValid) {
            const error = new ValidationDataError();

            let response = new ResponseError(res, error);
            await response.addMongooseErrors(model);

            const duplicateError = response.messages.find(
                message => message.description.includes('Name duplicated'));
            if (duplicateError) {
                response = new ResponseError(res, new DuplicateWarning(
                    `${duplicateError.name} name`));
            }

            response.send();
            return;
        }

        const doc = await model.save();

        const response = new ResponseSuccess<Document>(res);
        response.send(doc.id);
    }

    /**
     * Get configuration by ID, if not found send a `NotFoundWarning` over a 
     * `ResponseError` instance.
     *
     * @param res Response from Express
     * @param id Configuration ID
     * @returns a promise containing either a `Config` object or a 
     *  `ResponseError` instance
     */
    private async getConfigById(res: express.Response, id: string): 
        Promise<Config | ResponseError> {
        if (!mongoose.Types.ObjectId.isValid(id)) {
            const error = new InvalidIDError(id);
            return new ResponseError(res, error);
        }

        const config = await this.configRepo.findOneById(id);
        if (!config) {
            return new ResponseError(res, new NotFoundWarning());
        }

        return config;
    }

    /**
     * Create a bkp to comparison on alerter
     * @param config  Current official config
     */
    private async createBkp(config : Document<Config>) : Promise<void> {        
        await ConfigOldModel.deleteOne({ _id: config._id });
        const oldModel : Document<Config> = new ConfigOldModel(
            config.toObject()
        );
        await oldModel.save();
    }
}
