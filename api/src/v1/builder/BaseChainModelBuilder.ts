import mongoose, {Model, Schema} from "mongoose";
import {BaseChain} from "../../../../entities/ts/BaseChain";
import {Collection, ModelName} from "../../constant/mongoose";
import {MongooseUtil} from "../../util/MongooseUtil";
import {ObjectUtil} from "../../util/ObjectUtil";
import {BaseMongoose} from "../entity/model/BaseMongoose";
import {IModelBuilder} from "./IModelBuilder";

/**
 * Builder to create Mongoose Schema and Model of BaseChain Entity
 */
export class BaseChainModelBuilder implements IModelBuilder<BaseChain> {

    private _schema: Schema = null;
    private _model: Model<BaseChain> = null;

    public produceSchema(): void {

        const entity = {} as BaseChain;
        entity.value = {
            type: String,
            required: [true, 'Value is required!'],
            default: null
        } as any;
        entity.sources = [{
            type: Schema.Types.ObjectId,
            ref: ModelName.GENERIC
        } as any];
        entity.thresholdAlerts = [{
            type: Schema.Types.ObjectId,
            ref: ModelName.GENERIC,
            alias: 'thresholdAlerts'
        } as any];
        entity.severityAlerts = [{
            type: Schema.Types.ObjectId,
            ref: ModelName.SEVERITY_ALERT_SUBCONFIG,
            alias: 'severityAlerts'
        } as any];
        entity.timeWindowAlerts = [{
            type: Schema.Types.ObjectId,
            ref: ModelName.GENERIC,
            alias: 'timeWindowAlerts'
        } as any];

        const obj = Object.assign(entity, new BaseMongoose());
        this._schema = new Schema(ObjectUtil.camelToSnake<object>(obj),
            {versionKey: false});

        MongooseUtil.virtualize(this._schema);
    }

    public produceModel(): void {
        this._model = mongoose.model(
            ModelName.BASE_CHAIN,
            this._schema,
            Collection.BASE_CHAIN
        ) as Model<BaseChain>;
    }

    public get model(): Model<BaseChain> {
        return this._model;
    }

    public get schema(): Schema {
        return this._schema;
    }
}
