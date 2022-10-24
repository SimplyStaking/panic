import mongoose, {Model, Schema} from 'mongoose';
import {Collection, ModelName} from '../../../constant/mongoose';
import {IModelBuilder} from '../IModelBuilder';
import {ObjectUtil} from '../../../util/ObjectUtil';
import {PagerDutyChannel} from "../../../../../entities/ts/channels/PagerDutyChannel";
import {MongooseUtil} from "../../../util/MongooseUtil";
import {StringUtil} from '../../../util/StringUtil';

/**
 * Builder to create Mongoose Schema and Model of PagerDuty Entity
 */
export class PagerDutyModelBuilder implements IModelBuilder<PagerDutyChannel> {

    private _schema: Schema = null;
    private _model: Model<PagerDutyChannel> = null;

    public produceSchema(): void {

        const entity = {} as PagerDutyChannel;

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
        entity.integrationKey = {
            type: String,
            alias: 'integrationKey',
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
            ModelName.PAGER_DUTY,
            this._schema,
            Collection.CONFIG
        ) as Model<PagerDutyChannel>;
    }

    public get model(): Model<PagerDutyChannel> {
        return this._model;
    }

    public get schema(): Schema {
        return this._schema;
    }
}
