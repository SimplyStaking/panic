import {Model, Schema} from "mongoose";
import {ContractSubconfig} from "../../../../entities/ts/ContractSubconfig";
import {MongooseUtil} from "../../util/MongooseUtil";
import {ObjectUtil} from "../../util/ObjectUtil";
import {BaseMongoose} from "../entity/model/BaseMongoose";
import {IModelBuilder} from "./IModelBuilder";

/**
 * Builder to create Mongoose Schema of ContractSubconfig Entity
 */
export class ContractSubconfigModelBuilder
    implements IModelBuilder<ContractSubconfig> {

    private _schema: Schema = null;
    private _model: Model<ContractSubconfig> = null;

    public produceSchema(): void {

        const contract = {} as ContractSubconfig;
        contract.url = {
            type: String,
            required: [true, 'Url of contract is required!']
        } as any;
        contract.monitor = Boolean as any;

        const obj = Object.assign(contract, new BaseMongoose());
        this._schema = new Schema(ObjectUtil.camelToSnake<object>(obj),
            {versionKey: false});

        MongooseUtil.virtualize(this._schema);

    }

    public produceModel(): void {
        this._model = null;
    }

    public get model(): Model<ContractSubconfig> {
        return this._model;
    }

    public get schema(): Schema {
        return this._schema;
    }
}
