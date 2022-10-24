import express from "express";
import {AbstractChannel, Channel} from "../../../../../entities/ts/channels/AbstractChannel";
import {EmailChannel} from "../../../../../entities/ts/channels/EmailChannel";
import {OpsgenieChannel} from "../../../../../entities/ts/channels/OpsgenieChannel";
import {PagerDutyChannel} from "../../../../../entities/ts/channels/PagerDutyChannel";
import {SlackChannel} from "../../../../../entities/ts/channels/SlackChannel";
import {TelegramChannel} from "../../../../../entities/ts/channels/TelegramChannel";
import {TwilioChannel} from "../../../../../entities/ts/channels/TwilioChannel";
import {Generic} from "../../../../../entities/ts/Generic";
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
import {ResponseError, ResponseNoContent, ResponseSuccess} from "../../entity/io/ResponseData";
import {
    EmailRepository,
    OpsgenieRepository,
    PagerDutyRepository,
    SlackRepository,
    TelegramRepository,
    TwilioRepository
} from "../../entity/repository/ChannelRepository";
import mongoose, {Document, Model} from "mongoose";
import {MongooseUtil} from "../../../util/MongooseUtil";
import {EmailModel} from "../../entity/model/channels/EmailModel";
import {OpsgenieModel} from "../../entity/model/channels/OpsgenieModel";
import {PagerDutyModel} from "../../entity/model/channels/PagerDutyModel";
import {SlackModel} from "../../entity/model/channels/SlackModel";
import {TelegramModel} from "../../entity/model/channels/TelegramModel";
import {TwilioModel} from "../../entity/model/channels/TwilioModel";
import {GenericRepository} from "../../entity/repository/GenericRepository";
import {ObjectID} from "mongodb";
import {GenericDocument} from "../../../constant/mongoose";
import {ObjectUtil} from "../../../util/ObjectUtil";
import {ConfigRepository} from "../../entity/repository/ConfigRepository";
import { EmailOldModel } from "../../entity/model/channels/EmailOldModel";
import { OpsgenieOldModel } from "../../entity/model/channels/OpsgenieOldModel";
import { PagerDutyOldModel } from "../../entity/model/channels/PagerDutyOldModel";
import { SlackOldModel } from "../../entity/model/channels/SlackOldModel";
import { TelegramOldModel } from "../../entity/model/channels/TelegramOldModel ";
import { TwillioOldModelBuilder } from "../../builder/channels/TwilioOldModelBuilder";
import { TwilioOldModel } from "../../entity/model/channels/TwilioOldModel";

/**
 * Resource Controller for Panic Channel
 */
export class ChannelResource {
    private readonly emailRepo: EmailRepository = null;
    private readonly opsgenieRepo: OpsgenieRepository = null;
    private readonly pagerDutyRepo: PagerDutyRepository = null;
    private readonly slackRepo: SlackRepository = null;
    private readonly telegramRepo: TelegramRepository = null;
    private readonly twilioRepo: TwilioRepository = null;

    private readonly genericRepo: GenericRepository = null;
    private readonly configRepo: ConfigRepository = null;

    constructor() {
        this.emailRepo = new EmailRepository();
        this.opsgenieRepo = new OpsgenieRepository();
        this.pagerDutyRepo = new PagerDutyRepository();
        this.slackRepo = new SlackRepository();
        this.telegramRepo = new TelegramRepository();
        this.twilioRepo = new TwilioRepository();

        this.genericRepo = new GenericRepository();
        this.configRepo = new ConfigRepository();
    }

    /**
     * Get a list of Channels from Database from channel collections
     *
     * @param req Request from Express
     * @param res Response from Express
     */
    public async getAll(req: express.Request,
                        res: express.Response): Promise<void> {
        try {
            const fieldsToPopulate: string[] = ['type'];
            const populateObject = {path: 'configs', select: 'sub_chain.name'};
            const emailChannels = await this.emailRepo.findAllByAndDeepPopulate(fieldsToPopulate, populateObject);
            const opsgenieChannels = await this.opsgenieRepo.findAllByAndDeepPopulate(fieldsToPopulate, populateObject);
            const pagerDutyChannels = await this.pagerDutyRepo.findAllByAndDeepPopulate(fieldsToPopulate, populateObject);
            const slackChannels = await this.slackRepo.findAllByAndDeepPopulate(fieldsToPopulate, populateObject);
            const telegramChannels = await this.telegramRepo.findAllByAndDeepPopulate(fieldsToPopulate, populateObject);
            const twilioChannels = await this.twilioRepo.findAllByAndDeepPopulate(fieldsToPopulate, populateObject);

            const channels: Channel[] = [].concat(emailChannels, opsgenieChannels,
                pagerDutyChannels, slackChannels, telegramChannels, twilioChannels);

            const response = new ResponseSuccess<Channel[]>(res);
            response.send(channels);
        } catch (err: any) {
            console.error(err);
            const error = new CouldNotRetrieveDataFromDB();
            const response = new ResponseError(res, error);
            response.send();
        }
    }

    /**
     * Get channel by id from Database from channel collections
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

            let channel = await this.getChannelById(res, req.params.id);
            if (channel instanceof ResponseError) {
                channel.send();
                return;
            }

            const response = new ResponseSuccess<Channel>(res);
            response.send(channel);
        } catch (err: any) {
            console.error(err);
            const error = new CouldNotRetrieveDataFromDB();
            const response = new ResponseError(res, error);
            response.send();
        }
    }

    /**
     * Gets a channel by ID, if not found send a `NotFoundWarning` over a `ResponseError` instance.
     *
     * @param res Response from Express
     * @param id Channel ID
     * @returns a promise containing either a `Channels` object or a `ResponseError` instance
     */
    private async getChannelById(res: express.Response, id: string): Promise<Channel | ResponseError> {
        const isValid = mongoose.Types.ObjectId.isValid(id);
        if (!isValid) {
            const error = new InvalidIDError(id);
            return new ResponseError(res, error);
        }

        const allRepos = [
            this.emailRepo, this.opsgenieRepo, this.pagerDutyRepo,
            this.slackRepo, this.telegramRepo, this.twilioRepo
        ];

        let channel: Channel = null;

        for (const repo of allRepos) {
            if (!channel) {
                channel = await repo.findOneByAndDeepPopulate(
                    id, ['type'],
                    {path: 'configs', select: 'sub_chain.name'}
                );
            }
        }

        if (!channel) {
            return new ResponseError(res, new NotFoundWarning());
        }

        return channel;
    }

    /**
     * Create a new Channel on Database in respective channel collection
     *
     * @param req Request from Express
     * @param res Response from Express
     */
    public async create(req: express.Request,
                        res: express.Response): Promise<void> {
        try {
            const channelType = await this.checkChannelTypeOnCreate(req, res);
            if (channelType instanceof ResponseError) {
                channelType.send();
                return;
            }

            delete req.body.type;
            // @ts-ignore
            req.body['type'] = channelType._id.toString();

            const invalidFields = ['configs'];
            const ChannelModel = ChannelResource.getModelByChannelTypeValue(channelType.value);
            const initialisedChannelObject = ChannelResource.getInitialisedObjectByChannelTypeValue(channelType.value);
            if (!ChannelModel || !initialisedChannelObject) {
                const error = new ValidationDataError();
                error.description += ' Unrecognised channel type.';
                const response = new ResponseError(res, error);
                response.send();
            }
            let channel: Channel = MongooseUtil.merge(initialisedChannelObject, req.body, invalidFields);
            let model: Document<Channel> = new ChannelModel(channel.toJSON());

            // For channel name duplication validation, we can use email repo
            // since we are using the same collection for channels/configs.
            let duplicate = await this.emailRepo.isDuplicateChannelName(channel);
            if (duplicate) {
                const response = new ResponseError(res,
                    new DuplicateWarning('name'));
                response.send();
                return;
            }

            await this.save(res, model, channelType.value);
        } catch (err: any) {
            console.error(err);
            const error = new CouldNotSaveDataToDB();
            const response = new ResponseError(res, error);
            response.send();
        }
    }

    public async checkChannelTypeOnCreate(req: express.Request,
                                          res: express.Response): Promise<Generic | ResponseError> {
        if (!('type' in req.body) || typeof req.body.type.id !== 'string') {
            const error = new ValidationDataError();
            error.description += ' Field type not specified or is not a string.';
            return new ResponseError(res, error);
        }
        const channelType = await this.genericRepo.findOneByGroupAndId('channel_type', req.body.type.id);

        if (!channelType) {
            const error = new ValidationDataError();
            error.description += ` Channel type with id ${req.body.type.id} not found.`;
            return new ResponseError(res, error);
        }

        return channelType;
    }

    /**
     * Returns the config type ID for the given channel type value.
     *
     * @param channelTypeValue the value of the channel type as a string
     * @returns config type ID for a channel if type corresponds to a channel, null otherwise
     */
    private static getConfigTypeIdByChannelTypeValue(channelTypeValue: string): GenericDocument | null {
        switch (channelTypeValue.toLowerCase()) {
            case 'email':
                return GenericDocument.CONFIG_TYPE_EMAIL_CHANNEL;
            case 'opsgenie':
                return GenericDocument.CONFIG_TYPE_OPSGENIE_CHANNEL;
            case 'pagerduty':
                return GenericDocument.CONFIG_TYPE_PAGERDUTY_CHANNEL;
            case 'slack':
                return GenericDocument.CONFIG_TYPE_SLACK_CHANNEL;
            case 'telegram':
                return GenericDocument.CONFIG_TYPE_TELEGRAM_CHANNEL;
            case 'twilio':
                return GenericDocument.CONFIG_TYPE_TWILIO_CHANNEL;
            default:
                return null;
        }
    }

    /**
     * Save document in channel collections. If an error occurs, an error response is sent via `res`.
     *
     * @param res Response from Express
     * @param model The channel document object
     * @param channelTypeValue The value of the channel type for Channel document passed
     */
    private async save(res: express.Response, model: Document<Channel>,
                       channelTypeValue: string): Promise<void> {
        const isValid = await MongooseUtil.isValid(model);
        if (!isValid) {
            const error = new ValidationDataError();
            const response = new ResponseError(res, error);
            await response.addMongooseErrors(model);
            response.send();
            return;
        }

        model.set('config_type', new ObjectID(
            ChannelResource.getConfigTypeIdByChannelTypeValue(channelTypeValue)));

        const doc = await model.save();

        const response = new ResponseSuccess<Document>(res);
        response.send(doc.id);
    }

    /**
     * Returns a model for the given channel type value.
     *
     * @param channelTypeValue the value of the channel type as a string
     * @returns a Model for a channel if type corresponds to a channel, null otherwise
     */
    private static getModelByChannelTypeValue(channelTypeValue: string): Model<any> | null {
        switch (channelTypeValue.toLowerCase()) {
            case 'email':
                return EmailModel;
            case 'opsgenie':
                return OpsgenieModel;
            case 'pagerduty':
                return PagerDutyModel;
            case 'slack':
                return SlackModel;
            case 'telegram':
                return TelegramModel;
            case 'twilio':
                return TwilioModel;
            default:
                return null;
        }
    }

    /**
     * Returns an initialised object corresponding to the given channel type value.
     *
     * @param channelTypeValue the value of the channel type as a string
     * @returns an initialised object for a channel if type corresponds to a channel, null otherwise
     */
    private static getInitialisedObjectByChannelTypeValue(channelTypeValue: string): Channel | null {
        switch (channelTypeValue.toLowerCase()) {
            case 'email':
                return new EmailChannel();
            case 'opsgenie':
                return new OpsgenieChannel();
            case 'pagerduty':
                return new PagerDutyChannel();
            case 'slack':
                return new SlackChannel();
            case 'telegram':
                return new TelegramChannel();
            case 'twilio':
                return new TwilioChannel();
            default:
                return null;
        }
    }

    /**
     * Updates an existing Channel on the Database in respective channel collection
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

            // to avoid updating certain fields update
            ['type', 'configs'].forEach((field) => {
                if (field in req.body) {
                    delete req.body[field];
                }
            });

            // For channel name duplication validation, we can use email repo
            // since we are using the same collection for channels/configs.
            let duplicate = await this.emailRepo.isDuplicateChannelName({
                ...req.body,
                id: req.params.id
            } as Channel);

            if (duplicate) {
                const response = new ResponseError(res,
                    new DuplicateWarning('name'));
                response.send();
                return;
            }

            const channel = await this.getChannelById(res, req.params.id);
            if (channel instanceof ResponseError) {
                channel.send();
                return;
            }

            await this.createBkp(channel);

            const request = ObjectUtil.deepCamelToSnake(req.body);
            const model: Document = MongooseUtil.merge(channel, request);               

            await this.save(res, model, channel.type.value);
        } catch (err: any) {
            console.error(err);
            const error = new CouldNotSaveDataToDB();
            const response = new ResponseError(res, error);
            response.send();
        }
    }

    /**
     * Removes a Channel by ID on Database in respective channel collection
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

            const channel = await this.emailRepo.findOneById(req.params.id);
            this.createBkp(channel as any);

            // Here we can use email repo since we are using the same collections
            // and IDs are always unique.
            const isDeleted = await this.emailRepo.deleteOneById(req.params.id);
            if (!isDeleted) {
                const response = new ResponseError(res, new NotFoundWarning());
                response.send();
                return;
            }

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
     * Create a link between a channel and a config on Database
     *
     * @param req Request from Express
     * @param res Response from Express
     */
    public async createConfigLink(req: express.Request,
                                  res: express.Response): Promise<void> {
        try {
            const config_id = await this.configValidation(req, res);

            if (config_id) {

                const channel = await this.getChannelById(
                    res, req.params.channel_id);

                if (channel instanceof ResponseError) {
                    channel.send();
                    return;
                }

                await this.createBkp(channel);


                // Here we can use email repo since we are using the same collections
                // and IDs are always unique.
                const result = await this.emailRepo.linkConfigToChannel(req.params.channel_id, config_id);

                if (result.matchedCount < 1) {
                    const response = new ResponseError(res, new NotFoundWarning());
                    response.send();
                    return;
                }

                const response = new ResponseNoContent(res);
                response.send();
            }
        } catch (err: any) {
            console.error(err);
            const error = new CouldNotSaveDataToDB();
            const response = new ResponseError(res, error);
            response.send();
        }
    }

    /**
     * Removes a link between a channel and a config on Database
     *
     * @param req Request from Express
     * @param res Response from Express
     */
    public async removeConfigLink(req: express.Request,
                                  res: express.Response): Promise<void> {
        try {
            const config_id = await this.configValidation(req, res);

            if (config_id) {

                const channel = await this.getChannelById(
                    res, req.params.channel_id);
                    
                if (channel instanceof ResponseError) {
                    channel.send();
                    return;
                }

                await this.createBkp(channel);

                // Here we can use email repo since we are using the same collections
                // and IDs are always unique.
                const result = await this.emailRepo.unlinkConfigFromChannel(req.params.channel_id, config_id);

                if (result.matchedCount < 1) {
                    const response = new ResponseError(res, new NotFoundWarning());
                    response.send();
                    return;
                }

                const response = new ResponseNoContent(res);
                response.send();
            }
        } catch (err: any) {
            console.error(err);
            const error = new CouldNotSaveDataToDB();
            const response = new ResponseError(res, error);
            response.send();
        }
    }

    /**
     * Validates configs request by checking params and config IDs
     *
     * @param req Request from Express
     * @param res Response from Express
     * @returns config id if validation is successful, else null
     */
    private async configValidation(req: express.Request, res: express.Response): Promise<string> {
        const responseError = this.isMissingParam(req, res, true);
        if (responseError instanceof ResponseError) {
            responseError.send();
            return null;
        }

        const config = await this.configRepo.findOneById(req.params.config_id);
        if (!config) {
            const response = new ResponseError(res, new NotFoundWarning());
            response.send();
            return null;
        }

        return config.id;
    }

    /**
     * Checks if there are missing params and that params are valid
     *
     * @param req Request from Express
     * @param res Response from Express
     * @param channelConfigIdsCheck whether to check for channel and config IDs instead of a single id
     *
     * @returns {@link ResponseError} instance if missing/invalid params, else null
     */
    private isMissingParam(req: express.Request, res: express.Response,
                           channelConfigIdsCheck: boolean = false): ResponseError | null {
        if (!channelConfigIdsCheck && !req.params.id) {
            const error = new MissingParameterWarning('id');

            return new ResponseError(res, error);
        }

        if (channelConfigIdsCheck && (!req.params.channel_id || !req.params.config_id)) {
            const error = new MissingParameterWarning(!req.params.channel_id ? 'channel_id' : 'config_id');

            return new ResponseError(res, error);
        }

        if (!channelConfigIdsCheck && !mongoose.Types.ObjectId.isValid(req.params.id)) {
            const error = new InvalidIDError(req.params.id);
            return new ResponseError(res, error);
        }

        if (channelConfigIdsCheck && (!mongoose.Types.ObjectId.isValid(req.params.channel_id) ||
            !mongoose.Types.ObjectId.isValid(req.params.config_id))) {
            const error = new InvalidIDError(
                !mongoose.Types.ObjectId.isValid(req.params.channel_id) ? req.params.channel_id : req.params.config_id);
            return new ResponseError(res, error);
        }

        return null;
    }


    /**
     * Create a bkp to comparison on alerter
     * @param channel  Current official config
     */
     private async createBkp(channel : AbstractChannel) : Promise<void> { 
        try {
            if(!channel) {
                return;
            }      
            
            const type = channel['config_type']['_id'].toString();
            let model : Model<Channel> = null;
    
            if(type === GenericDocument.CONFIG_TYPE_EMAIL_CHANNEL){
                model = EmailOldModel;
            } else if(type === GenericDocument.CONFIG_TYPE_OPSGENIE_CHANNEL){
                model = OpsgenieOldModel;
            } else if(type === GenericDocument.CONFIG_TYPE_PAGERDUTY_CHANNEL){
                model = PagerDutyOldModel;
            } else if(type === GenericDocument.CONFIG_TYPE_SLACK_CHANNEL){
                model = SlackOldModel;
            } else if(type === GenericDocument.CONFIG_TYPE_TELEGRAM_CHANNEL){
                model = TelegramOldModel;
            } else if(type === GenericDocument.CONFIG_TYPE_TWILIO_CHANNEL){
                model = TwilioOldModel;
            } else {
                return;
            }
    
            await model.deleteOne({ _id: channel.id });
            channel = channel['toObject']();
            const oldModel : Document<AbstractChannel> = new model(channel);        
            await oldModel.save();
        } catch(err) {
            console.error(err);
            return;
        }        
    }
}
