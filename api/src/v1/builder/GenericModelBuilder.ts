import mongoose, {Model, Schema} from 'mongoose';
import {Generic} from '../../../../entities/ts/Generic';
import {BaseMongoose} from '../entity/model/BaseMongoose';
import {IModelBuilder} from './IModelBuilder';
import {Collection, ModelName} from '../../constant/mongoose';
import {MongooseUtil} from "../../util/MongooseUtil";

/**
 * Builder to create Mongoose Schema and Model of Generic Entity
 */
export class GenericModelBuilder implements IModelBuilder<Generic> {

    private _schema: Schema = null;
    private _model: Model<Generic> = null;

    public produceSchema(): void {

        const entity = {} as Generic;
        entity.description = {type: String, default: null} as any;
        entity.group = {
            type: String,
            required: [true, 'Group is required!'],
            default: null
        } as any;
        entity.value = {
            type: String,
            required: [true, 'Value is required!'],
            default: null
        } as any;

        const obj = Object.assign(entity, new BaseMongoose());
        this._schema = new Schema(obj as object,
            {versionKey: false});

        MongooseUtil.virtualize(this._schema);
    }

    public produceModel(): void {
        this._model = mongoose.model(
            ModelName.GENERIC,
            this._schema,
            Collection.GENERIC
        ) as Model<Generic>;
    }

    public get model(): Model<Generic> {
        return this._model;
    }

    public get schema(): Schema {
        return this._schema;
    }
}
