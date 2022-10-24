import mongoose, {Model, Schema} from "mongoose";
import {SeverityAlertSubconfig} from "../../../../entities/ts/SeverityAlertSubconfig";
import {ObjectUtil} from "../../util/ObjectUtil";
import {IModelBuilder} from "./IModelBuilder";
import {Collection, ModelName} from "../../constant/mongoose";
import {MongooseUtil} from "../../util/MongooseUtil";
import {StringUtil} from "../../util/StringUtil";

/**
 * Builder to create Mongoose Schema of SeverityAlertSubconfig Entity
 */
export class SeverityAlertSubconfigModelBuilder implements IModelBuilder<SeverityAlertSubconfig> {

    private _schema: Schema = null;
    private _model: Model<SeverityAlertSubconfig> = null;

    public produceSchema(): void {

        const entity = {} as SeverityAlertSubconfig;
        entity.status = {type: Boolean, default: true} as any;
        entity.created = {type: Date, default: Date.now} as any;
        entity.modified = {type: Date, default: null} as any;
        entity.name = {
            type: String,
            default: null,
            set: StringUtil.trim
        } as any;
        entity.value = {type: String, default: null} as any;
        entity.description = {type: String, default: null} as any;
        entity.group = {type: String, default: null} as any;
        entity.type = {
            type: Schema.Types.ObjectId,
            ref: ModelName.GENERIC,
            required: [true, 'Severity type is required!'],
        } as any;
        entity.enabled = {type: Boolean, default: true} as any;

        this._schema = new Schema(ObjectUtil.camelToSnake<object>(entity),
            {versionKey: false});
        MongooseUtil.virtualize(this._schema);
    }

    public produceModel(): void {
        this._model = mongoose.model(
            ModelName.SEVERITY_ALERT_SUBCONFIG,
            this._schema,
            Collection.GENERIC
        ) as Model<SeverityAlertSubconfig>;
    }

    public get model(): Model<SeverityAlertSubconfig> {
        return this._model;
    }

    public get schema(): Schema {
        return this._schema;
    }
}
