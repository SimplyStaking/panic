import mongoose, {Model, Schema} from 'mongoose';
import {Collection, ModelName} from '../../../constant/mongoose';
import {IModelBuilder} from '../IModelBuilder';
import {ObjectUtil} from '../../../util/ObjectUtil';
import {EmailChannel} from "../../../../../entities/ts/channels/EmailChannel";
import {MongooseUtil} from "../../../util/MongooseUtil";
import {StringUtil} from '../../../util/StringUtil';

/**
 * Builder to create Mongoose Schema and Model of Email Entity
 */
export class EmailModelBuilder implements IModelBuilder<EmailChannel> {

    private _schema: Schema = null;
    private _model: Model<EmailChannel> = null;

    public produceSchema(): void {

        const entity = {} as EmailChannel;

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
        entity.smtp = {
            type: String,
            default: null
        } as any;
        entity.port = {
            type: Number,
            default: null
        } as any;
        entity.emailFrom = {
            type: String,
            alias: 'emailFrom',
            default: null
        } as any;
        entity.emailsTo = {
            type: [String],
            alias: 'emailsTo'
        } as any;
        entity.username = {
            type: String,
            default: null
        } as any;
        entity.password = {
            type: String,
            default: null
        } as any;
        entity.info = {
            type: Boolean,
            default: false
        } as any;
        entity.warning = {
            type: Boolean,
            default: false
        } as any;
        entity.critical = {
            type: Boolean,
            default: false
        } as any;
        entity.error = {
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
            ModelName.EMAIL,
            this._schema,
            Collection.CONFIG
        ) as Model<EmailChannel>;
    }

    public get model(): Model<EmailChannel> {
        return this._model;
    }

    public get schema(): Schema {
        return this._schema;
    }
}
