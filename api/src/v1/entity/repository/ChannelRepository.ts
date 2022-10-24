import {Channel} from "../../../../../entities/ts/channels/AbstractChannel";
import {EmailChannel} from "../../../../../entities/ts/channels/EmailChannel";
import {OpsgenieChannel} from "../../../../../entities/ts/channels/OpsgenieChannel";
import {PagerDutyChannel} from "../../../../../entities/ts/channels/PagerDutyChannel";
import {SlackChannel} from "../../../../../entities/ts/channels/SlackChannel";
import {TelegramChannel} from "../../../../../entities/ts/channels/TelegramChannel";
import {TwilioChannel} from "../../../../../entities/ts/channels/TwilioChannel";
import {AbstractRepository} from "./AbstractRepository";
import {EmailModel} from "../model/channels/EmailModel";
import {OpsgenieModel} from "../model/channels/OpsgenieModel";
import {PagerDutyModel} from "../model/channels/PagerDutyModel";
import {SlackModel} from "../model/channels/SlackModel";
import {TelegramModel} from "../model/channels/TelegramModel";
import {TwilioModel} from "../model/channels/TwilioModel";
import mongoose, {UpdateWriteOpResult} from "mongoose";
import {ObjectID} from "mongodb";
import {GenericDocument} from "../../../constant/mongoose";

/**
 * Implements specific operations for all Channel models
 */
class ChannelRepository<T extends Channel> extends AbstractRepository<T> {
    public constructor(protected model: mongoose.Model<T>) {
        super(model);
    }

    /**
     * Return a list of channels from database and populate references
     *
     * @param fieldsToPopulate reference fields to populate within documents
     * @param config_type_id the id of the config type to be returned
     * @param populateObject object which contains information regarding deep population
     * @returns an array of channels with populated references
     */
    public async findAllByAndDeepPopulate(fieldsToPopulate: string[], config_type_id: string,
                                          populateObject): Promise<Array<T>> {
        return this.model.find({
            config_type: new ObjectID(config_type_id)
        }).populate(fieldsToPopulate).populate(populateObject);
    }

    /**
     * Returns a channel from database by id and populate references
     *
     * @param id The mongo hash id
     * @param fieldsToPopulate reference fields to populate within document
     * @param config_type_id the id of the config type to be returned
     * @param populateObject object which contains information regarding deep population
     * @returns channel with populated references
     */
    public async findOneByAndDeepPopulate(id: string, fieldsToPopulate: string[], config_type_id: string,
                                          populateObject): Promise<any> {
        return this.model.findOne({
            _id: id,
            config_type: new ObjectID(config_type_id)
        }).populate(fieldsToPopulate).populate(populateObject);
    }

    /**
     * Creates a link between a channel and a config by adding the
     * config id to the array of configs in channel document.
     *
     * @param channel_id The mongo hash id of the channel document
     * @param config_id The mongo hash id of the config document
     * @returns update result
     */
    public async linkConfigToChannel(channel_id: string, config_id: string): Promise<UpdateWriteOpResult> {
        return this.model.updateOne(
            {_id: channel_id, config_type: {$ne: new ObjectID(GenericDocument.CONFIG_TYPE_SUB_CHAIN)}},
            // @ts-ignore
            {$addToSet: {configs: new ObjectID(config_id)}}
        );
    }

    /**
     * Removes the link between a channel and a config by removing the
     * config id from the array of configs in channel document.
     *
     * @param channel_id The mongo hash id of the channel document
     * @param config_id The mongo hash id of the config document
     * @returns update result
     */
    public async unlinkConfigFromChannel(channel_id: string, config_id: string): Promise<UpdateWriteOpResult> {
        return this.model.updateOne(
            {_id: channel_id, config_type: {$ne: new ObjectID(GenericDocument.CONFIG_TYPE_SUB_CHAIN)}},
            // @ts-ignore
            {$pull: {configs: new ObjectID(config_id)}}
        );
    }

    /**
     * Removes the link between all channels and a config by removing the
     * config id from the array of configs in channel documents (if any).
     *
     * @param config_id The mongo hash id of the config document
     * @returns update result
     */
    public async unlinkConfigFromAllChannels(config_id: string): Promise<UpdateWriteOpResult> {
        return this.model.updateMany(
            {config_type: {$ne: new ObjectID(GenericDocument.CONFIG_TYPE_SUB_CHAIN)}},
            // @ts-ignore
            {$pull: {configs: new ObjectID(config_id)}}
        );
    }

    /**
     * Check if channel name already exists on Database
     *
     * @param channel The channel or request object
     * @returns true if channel name exists, otherwise false
     */
    public async isDuplicateChannelName(channel: Channel): Promise<Boolean> {
        if ('name' in channel) {
            const criteria = {
                name: channel.name
            }

            // for edit case, to ignore self register
            const isValidConfigID = 'id' in channel && mongoose.Types.ObjectId.isValid(channel.id);

            if (isValidConfigID) {
                criteria['_id'] = {'$ne': new ObjectID(channel.id)};
            }

            const channels = await this.findBy(criteria);
            return channels && channels.length > 0;
        }

        return false;
    }
}

/**
 * Implements specific operations for Email model in database
 */
export class EmailRepository extends ChannelRepository<EmailChannel> {
    public constructor() {
        super(EmailModel);
    }

    /**
     * Return a list of Email channels from database and populate references
     *
     * @param fieldsToPopulate reference fields to populate within documents
     * @param populateObject object which contains information regarding deep population
     * @returns an array of Email channels with populated references
     */
    public async findAllByAndDeepPopulate(fieldsToPopulate: string[],
                                          populateObject): Promise<Array<EmailChannel>> {
        return super.findAllByAndDeepPopulate(
            fieldsToPopulate, GenericDocument.CONFIG_TYPE_EMAIL_CHANNEL, populateObject);
    }

    /**
     * Returns an Email channel from database by id and populate references
     *
     * @param id The mongo hash id
     * @param fieldsToPopulate reference fields to populate within document
     * @param populateObject object which contains information regarding deep population
     * @returns Email channel with populated references
     */
    public async findOneByAndDeepPopulate(id: string, fieldsToPopulate: string[],
                                          populateObject): Promise<any> {
        return super.findOneByAndDeepPopulate(
            id, fieldsToPopulate, GenericDocument.CONFIG_TYPE_EMAIL_CHANNEL, populateObject);
    }
}

/**
 * Implements specific operations for Opsgenie model in database
 */
export class OpsgenieRepository extends ChannelRepository<OpsgenieChannel> {
    public constructor() {
        super(OpsgenieModel);
    }

    /**
     * Return a list of Opsgenie channels from database and populate references
     *
     * @param fieldsToPopulate reference fields to populate within documents
     * @param populateObject object which contains information regarding deep population
     * @returns an array of Opsgenie channels with populated references
     */
    public async findAllByAndDeepPopulate(fieldsToPopulate: string[],
                                          populateObject): Promise<Array<OpsgenieChannel>> {
        return super.findAllByAndDeepPopulate(
            fieldsToPopulate, GenericDocument.CONFIG_TYPE_OPSGENIE_CHANNEL, populateObject);
    }

    /**
     * Returns an Opsgenie channel from database by id and populate references
     *
     * @param id The mongo hash id
     * @param fieldsToPopulate reference fields to populate within document
     * @param populateObject object which contains information regarding deep population
     * @returns Opsgenie channel with populated references
     */
    public async findOneByAndDeepPopulate(id: string, fieldsToPopulate: string[],
                                          populateObject): Promise<any> {
        return super.findOneByAndDeepPopulate(
            id, fieldsToPopulate, GenericDocument.CONFIG_TYPE_OPSGENIE_CHANNEL, populateObject);
    }
}

/**
 * Implements specific operations for PagerDuty model in database
 */
export class PagerDutyRepository extends ChannelRepository<PagerDutyChannel> {
    public constructor() {
        super(PagerDutyModel);
    }

    /**
     * Return a list of PagerDuty channels from database and populate references
     *
     * @param fieldsToPopulate reference fields to populate within documents
     * @param populateObject object which contains information regarding deep population
     * @returns an array of PagerDuty channels with populated references
     */
    public async findAllByAndDeepPopulate(fieldsToPopulate: string[],
                                          populateObject): Promise<Array<PagerDutyChannel>> {
        return super.findAllByAndDeepPopulate(
            fieldsToPopulate, GenericDocument.CONFIG_TYPE_PAGERDUTY_CHANNEL, populateObject);
    }

    /**
     * Returns a PagerDuty channel from database by id and populate references
     *
     * @param id The mongo hash id
     * @param fieldsToPopulate reference fields to populate within document
     * @param populateObject object which contains information regarding deep population
     * @returns PagerDuty channel with populated references
     */
    public async findOneByAndDeepPopulate(id: string, fieldsToPopulate: string[],
                                          populateObject): Promise<any> {
        return super.findOneByAndDeepPopulate(
            id, fieldsToPopulate, GenericDocument.CONFIG_TYPE_PAGERDUTY_CHANNEL, populateObject);
    }
}

/**
 * Implements specific operations for Slack model in database
 */
export class SlackRepository extends ChannelRepository<SlackChannel> {
    public constructor() {
        super(SlackModel);
    }

    /**
     * Return a list of Slack channels from database and populate references
     *
     * @param fieldsToPopulate reference fields to populate within documents
     * @param populateObject object which contains information regarding deep population
     * @returns an array of Slack channels with populated references
     */
    public async findAllByAndDeepPopulate(fieldsToPopulate: string[],
                                          populateObject): Promise<Array<SlackChannel>> {
        return super.findAllByAndDeepPopulate(
            fieldsToPopulate, GenericDocument.CONFIG_TYPE_SLACK_CHANNEL, populateObject);
    }

    /**
     * Returns a Slack channel from database by id and populate references
     *
     * @param id The mongo hash id
     * @param fieldsToPopulate reference fields to populate within document
     * @param populateObject object which contains information regarding deep population
     * @returns Slack channel with populated references
     */
    public async findOneByAndDeepPopulate(id: string, fieldsToPopulate: string[],
                                          populateObject): Promise<any> {
        return super.findOneByAndDeepPopulate(
            id, fieldsToPopulate, GenericDocument.CONFIG_TYPE_SLACK_CHANNEL, populateObject);
    }
}

/**
 * Implements specific operations for Telegram model in database
 */
export class TelegramRepository extends ChannelRepository<TelegramChannel> {
    public constructor() {
        super(TelegramModel);
    }

    /**
     * Return a list of Telegram channels from database and populate references
     *
     * @param fieldsToPopulate reference fields to populate within documents
     * @param populateObject object which contains information regarding deep population
     * @returns an array of Telegram channels with populated references
     */
    public async findAllByAndDeepPopulate(fieldsToPopulate: string[],
                                          populateObject): Promise<Array<TelegramChannel>> {
        return super.findAllByAndDeepPopulate(
            fieldsToPopulate, GenericDocument.CONFIG_TYPE_TELEGRAM_CHANNEL, populateObject);
    }

    /**
     * Returns a Telegram channel from database by id and populate references
     *
     * @param id The mongo hash id
     * @param fieldsToPopulate reference fields to populate within document
     * @param populateObject object which contains information regarding deep population
     * @returns Telegram channel with populated references
     */
    public async findOneByAndDeepPopulate(id: string, fieldsToPopulate: string[],
                                          populateObject): Promise<any> {
        return super.findOneByAndDeepPopulate(
            id, fieldsToPopulate, GenericDocument.CONFIG_TYPE_TELEGRAM_CHANNEL, populateObject);
    }
}

/**
 * Implements specific operations for Twilio model in database
 */
export class TwilioRepository extends ChannelRepository<TwilioChannel> {
    public constructor() {
        super(TwilioModel);
    }

    /**
     * Return a list of Twilio channels from database and populate references
     *
     * @param fieldsToPopulate reference fields to populate within documents
     * @param populateObject object which contains information regarding deep population
     * @returns an array of Twilio channels with populated references
     */
    public async findAllByAndDeepPopulate(fieldsToPopulate: string[],
                                          populateObject): Promise<Array<TwilioChannel>> {
        return super.findAllByAndDeepPopulate(
            fieldsToPopulate, GenericDocument.CONFIG_TYPE_TWILIO_CHANNEL, populateObject);
    }

    /**
     * Returns a Twilio channel from database by id and populate references
     *
     * @param id The mongo hash id
     * @param fieldsToPopulate reference fields to populate within document
     * @param populateObject object which contains information regarding deep population
     * @returns Twilio channel with populated references
     */
    public async findOneByAndDeepPopulate(id: string, fieldsToPopulate: string[],
                                          populateObject): Promise<any> {
        return super.findOneByAndDeepPopulate(
            id, fieldsToPopulate, GenericDocument.CONFIG_TYPE_TWILIO_CHANNEL, populateObject);
    }
}
