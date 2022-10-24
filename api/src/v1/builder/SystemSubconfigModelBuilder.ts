import {Model, Schema} from "mongoose";
import {SystemSubconfig} from "../../../../entities/ts/SystemSubconfig";
import {MongooseUtil} from "../../util/MongooseUtil";
import {ObjectUtil} from "../../util/ObjectUtil";
import {BaseMongoose} from "../entity/model/BaseMongoose";
import {IModelBuilder} from "./IModelBuilder";

/**
 * Builder to create Mongoose Schema of SystemSubconfig Entity
 */
export class SystemSubconfigModelBuilder
    implements IModelBuilder<SystemSubconfig> {

    private _schema: Schema = null;
    private _model: Model<SystemSubconfig> = null;

    public produceSchema(): void {

        const entity = {} as SystemSubconfig;
        entity.monitor = {type: Boolean, default: null} as any;
        entity.exporterUrl = {
            type: String,
            alias: 'exporterUrl',
            default: null
        } as any;

        const obj = Object.assign(entity, new BaseMongoose());
        this._schema = new Schema(ObjectUtil.camelToSnake<object>(obj),
            {versionKey: false});

        MongooseUtil.virtualize(this._schema);
    }

    public produceModel(): void {
        this._model = null;
    }

    public get model(): Model<SystemSubconfig> {
        return this._model;
    }

    public get schema(): Schema {
        return this._schema;
    }
}
