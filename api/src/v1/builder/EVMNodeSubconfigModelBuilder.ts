import {Model, Schema} from "mongoose";
import {EVMNodeSubconfig} from "../../../../entities/ts/EVMNodeSubconfig";
import {MongooseUtil} from "../../util/MongooseUtil";
import {ObjectUtil} from "../../util/ObjectUtil";
import {BaseMongoose} from "../entity/model/BaseMongoose";
import {IModelBuilder} from "./IModelBuilder";

/**
 * Builder to create Mongoose Schema of EVMNodeSubconfig Entity
 */
export class EVMNodeSubconfigModelBuilder
    implements IModelBuilder<EVMNodeSubconfig> {

    private _schema: Schema = null;
    private _model: Model<EVMNodeSubconfig> = null;

    public produceSchema(): void {

        const entity = {} as EVMNodeSubconfig;
        entity.monitor = {
            type: Boolean,
            default: null
        } as any;
        entity.nodeHttpUrl = {
            type: String,
            alias: 'nodeHttpUrl',
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

    public get model(): Model<EVMNodeSubconfig> {
        return this._model;
    }

    public get schema(): Schema {
        return this._schema;
    }
}
