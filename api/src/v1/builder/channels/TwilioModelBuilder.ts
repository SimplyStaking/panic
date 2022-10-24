import mongoose, {Model, Schema} from 'mongoose';
import {Collection, ModelName} from '../../../constant/mongoose';
import {IModelBuilder} from '../IModelBuilder';
import {ObjectUtil} from '../../../util/ObjectUtil';
import {TwilioChannel} from "../../../../../entities/ts/channels/TwilioChannel";
import {MongooseUtil} from "../../../util/MongooseUtil";
import {StringUtil} from '../../../util/StringUtil';

/**
 * Builder to create Mongoose Schema and Model of Twilio Entity
 */
export class TwilioModelBuilder implements IModelBuilder<TwilioChannel> {

    private _schema: Schema = null;
    private _model: Model<TwilioChannel> = null;

    public produceSchema(): void {

        const entity = {} as TwilioChannel;

        entity.created = {
            type: Date,
            default: null
        } as any;
        entity.modified = {
            type: Date,
            default: null
        } as any;
        entity.name = {
            type: String,
            required: [true, 'Name is required!'],
            default: null,
            set: StringUtil.trim
        } as any;
        entity.type = {
            type: Schema.Types.ObjectId,
            ref: ModelName.GENERIC,
            required: [true, 'Type is required!'],
            default: null
        } as any;
        entity.configs = [{
            type: Schema.Types.ObjectId,
            ref: ModelName.CONFIG
        } as any];
        entity.accountSid = {
            type: String,
            alias: 'accountSid',
            default: null
        } as any;
        entity.authToken = {
            type: String,
            alias: 'authToken',
            default: null
        } as any;
        entity.twilioPhoneNumber = {
            type: String,
            alias: 'twilioPhoneNumber',
            default: null
        } as any;
        entity.twilioPhoneNumbersToDial = {
            type: [String],
            alias: 'twilioPhoneNumbersToDial'
        } as any;
        entity.critical = {
            type: Boolean,
            default: false
        } as any;
        entity['configType'] = {
            type: Schema.Types.ObjectId,
            ref: ModelName.GENERIC
        } as any;

        this._schema = new Schema(
            ObjectUtil.camelToSnake<object>(entity),
            {versionKey: false}
        );

        MongooseUtil.virtualize(this._schema);
    }

    public produceModel(): void {
        this._model = mongoose.model(
            ModelName.TWILIO,
            this._schema,
            Collection.CONFIG
        ) as Model<TwilioChannel>;
    }

    public get model(): Model<TwilioChannel> {
        return this._model;
    }

    public get schema(): Schema {
        return this._schema;
    }
}
