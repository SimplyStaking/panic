import {Model, Schema} from "mongoose";
import {SubChain} from "../../../../entities/ts/SubChain";
import {MongooseUtil} from "../../util/MongooseUtil";
import {ObjectUtil} from "../../util/ObjectUtil";
import {BaseMongoose} from "../entity/model/BaseMongoose";
import {IModelBuilder} from "./IModelBuilder";

/**
 * Builder to create Mongoose Schema of Sub chain Entity
 */
export class SubChainModelBuilder implements IModelBuilder<SubChain> {

    private _schema: Schema = null;
    private _model: Model<SubChain> = null;

    public produceSchema(): void {
        this._schema = new Schema(
            ObjectUtil.camelToSnake<object>(new BaseMongoose()),
            {versionKey: false}
        );

        MongooseUtil.virtualize(this._schema);
    }

    public produceModel(): void {
        this._model = null;
    }

    public get model(): Model<SubChain> {
        return this._model;
    }

    public get schema(): Schema {
        return this._schema;
    }
}
